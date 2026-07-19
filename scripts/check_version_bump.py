#!/usr/bin/env python3
"""Fail when plugin content changes without a plugin version bump.

Diffs the working tree against the merge base with --base (the PR's target
branch in CI). Any change under plugins/<plugin>/ requires that `version` in
plugins/<plugin>/.claude-plugin/plugin.json changed too: the plugin cache is
keyed by version, so an unbumped content change leaves consumers silently on
the stale copy. The same rule guards the canonical catalog: a change under
skills/ or an adapter's own directory requires a bump in that adapter's
manifest (.claude-plugin/plugin.json for Claude, .codex-plugin/plugin.json
for Codex — both hosts cache by version). Every path under a guarded root
counts as shipped content — a spurious patch bump is cheap, a stale cache is
not. Brand-new plugins (no manifest at base) and deleted plugins (no manifest
now) pass; bump-only diffs pass by construction.

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
ADAPTER_MANIFESTS = (
    (".claude-plugin/plugin.json", ("skills/", ".claude-plugin/")),
    (".codex-plugin/plugin.json", ("skills/", ".codex-plugin/", ".agents/")),
)


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


def version_at(ref: str, manifest_path: str, errors: list[str]) -> str | None:
    """Version recorded at `ref`, or None when the manifest does not exist there."""
    shown = run_git("show", f"{ref}:{manifest_path}")
    if shown.returncode != 0:
        return None
    return parse_version(shown.stdout, f"{manifest_path} at {ref}", errors)


def version_in_worktree(root: Path, manifest_path: str, errors: list[str]) -> str | None:
    try:
        raw = (root / manifest_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as exc:
        errors.append(f"{manifest_path}: cannot read UTF-8 file: {exc}")
        return None
    return parse_version(raw, manifest_path, errors)


def changed_paths(merge_base: str, errors: list[str]) -> list[str] | None:
    diff = run_git("diff", "--name-only", "-z", merge_base, "--")
    if diff.returncode != 0:
        errors.append(f"git diff against {merge_base} failed: {diff.stderr.strip()}")
        return None
    return [path for path in diff.stdout.split("\0") if path]


def check_manifest(
    root: Path,
    merge_base: str,
    manifest_path: str,
    guarded: str,
    errors: list[str],
) -> bool:
    """True when the manifest existed at both ends and was version-compared."""
    base_version = version_at(merge_base, manifest_path, errors)
    if base_version is None:
        return False  # new package, or its base manifest is already reported
    head_version = version_in_worktree(root, manifest_path, errors)
    if head_version is None:
        return False  # deleted package, or its manifest is already reported
    if head_version == base_version:
        errors.append(
            f"{guarded}: content changed but version stayed at {base_version!r}; "
            f"bump {manifest_path}"
        )
    return True


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

    paths = changed_paths(merge_base, errors)
    plugins: list[str] = []
    adapters: list[str] = []
    checked = 0
    if paths is not None:
        names: set[str] = set()
        for path in paths:
            parts = path.split("/")
            if len(parts) >= 3 and parts[0] == "plugins":
                names.add(parts[1])
        plugins = sorted(names)
        for plugin in plugins:
            manifest_path = f"plugins/{plugin}/{MANIFEST_SUFFIX}"
            checked += check_manifest(root, merge_base, manifest_path, f"plugins/{plugin}", errors)
        for manifest_path, roots in ADAPTER_MANIFESTS:
            hits = [guarded for guarded in roots if any(path.startswith(guarded) for path in paths)]
            if not hits:
                continue
            adapters.append(manifest_path)
            checked += check_manifest(root, merge_base, manifest_path, " + ".join(hits), errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not plugins and not adapters:
        print(f"OK: no plugin content changes relative to {base}.")
    else:
        print(
            f"OK: {len(plugins)} changed plugin(s) and {len(adapters)} touched adapter(s) "
            f"relative to {base}; {checked} version-checked."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
