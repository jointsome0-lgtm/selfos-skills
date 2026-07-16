#!/usr/bin/env python3
"""Fail when plugin content changes without a plugin version bump.

Diffs the working tree against the merge base with --base (the PR's target
branch in CI). Any change under plugins/<plugin>/ requires that `version` in
plugins/<plugin>/.claude-plugin/plugin.json changed too: the plugin cache is
keyed by version, so an unbumped content change leaves consumers silently on
the stale copy. Every path under a plugin counts as shipped content — a
spurious patch bump is cheap, a stale cache is not. Brand-new plugins (no
manifest at base) and deleted plugins (no manifest now) pass; bump-only diffs
pass by construction.

Operates on the git repository containing the current directory, so it works
in any checkout and in the self-test's fixture repositories.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_BASES = ("origin/main", "main")
MANIFEST_SUFFIX = ".claude-plugin/plugin.json"


def run_git(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *argv], capture_output=True, text=True)


def resolve_ref(ref: str) -> bool:
    return run_git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def parse_version(raw: str, where: str, errors: list[str]) -> str | None:
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"{where}: invalid JSON: {exc.msg}")
        return None
    version = manifest.get("version") if isinstance(manifest, dict) else None
    if not isinstance(version, str) or not version.strip():
        errors.append(f"{where}: missing or empty 'version' field")
        return None
    return version


def version_at(ref: str, plugin: str, errors: list[str]) -> str | None:
    """Version recorded at `ref`, or None when the manifest does not exist there."""
    manifest_path = f"plugins/{plugin}/{MANIFEST_SUFFIX}"
    shown = run_git("show", f"{ref}:{manifest_path}")
    if shown.returncode != 0:
        return None
    return parse_version(shown.stdout, f"{manifest_path} at {ref}", errors)


def version_in_worktree(root: Path, plugin: str, errors: list[str]) -> str | None:
    manifest_path = root / "plugins" / plugin / MANIFEST_SUFFIX
    relative = f"plugins/{plugin}/{MANIFEST_SUFFIX}"
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: cannot read UTF-8 file: {exc}")
        return None
    return parse_version(raw, relative, errors)


def changed_plugins(merge_base: str, errors: list[str]) -> list[str] | None:
    diff = run_git("diff", "--name-only", "-z", merge_base, "--")
    if diff.returncode != 0:
        errors.append(f"git diff against {merge_base} failed: {diff.stderr.strip()}")
        return None
    plugins: set[str] = set()
    for path in diff.stdout.split("\0"):
        parts = path.split("/")
        if len(parts) >= 3 and parts[0] == "plugins":
            plugins.add(parts[1])
    return sorted(plugins)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        help="ref to diff against via its merge base with HEAD "
        f"(default: first of {', '.join(DEFAULT_BASES)} that exists)",
    )
    args = parser.parse_args()

    errors: list[str] = []

    toplevel = run_git("rev-parse", "--show-toplevel")
    if toplevel.returncode != 0:
        print("ERROR: not inside a git repository", file=sys.stderr)
        return 1
    root = Path(toplevel.stdout.strip())

    base = args.base
    if base is None:
        base = next((ref for ref in DEFAULT_BASES if resolve_ref(ref)), None)
        if base is None:
            print(f"ERROR: none of {', '.join(DEFAULT_BASES)} exists; pass --base", file=sys.stderr)
            return 1
    elif not resolve_ref(base):
        print(f"ERROR: base ref {base!r} does not resolve to a commit", file=sys.stderr)
        return 1

    merged = run_git("merge-base", base, "HEAD")
    if merged.returncode != 0:
        print(f"ERROR: no merge base between {base!r} and HEAD: {merged.stderr.strip()}", file=sys.stderr)
        return 1
    merge_base = merged.stdout.strip()

    plugins = changed_plugins(merge_base, errors)
    checked = 0
    if plugins is not None:
        for plugin in plugins:
            base_version = version_at(merge_base, plugin, errors)
            if base_version is None:
                continue  # new plugin, or its base manifest is already reported
            head_version = version_in_worktree(root, plugin, errors)
            if head_version is None:
                continue  # deleted plugin, or its manifest is already reported
            checked += 1
            if head_version == base_version:
                errors.append(
                    f"plugins/{plugin}: content changed but version stayed at {base_version!r}; "
                    f"bump plugins/{plugin}/{MANIFEST_SUFFIX}"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not plugins:
        print(f"OK: no plugin content changes relative to {base}.")
    else:
        print(f"OK: {len(plugins)} changed plugin(s) relative to {base}; {checked} version-checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
