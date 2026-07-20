#!/usr/bin/env python3
"""Enforce the frozen legacy-plugin deprecation policy on pull-request diffs."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys


POLICY_PATH = "plugins/deprecation.json"
LABEL_KINDS = {
    "legacy-plugin-compatibility": "compatibility",
    "legacy-plugin-security": "security",
    "legacy-plugin-removal": "removal",
}


def run_git(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *argv], capture_output=True, text=True)


def read_policy(raw: str, where: str, errors: list[str]) -> dict | None:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"{where}: invalid JSON: {exc.msg}")
        return None
    if not isinstance(value, dict) or not isinstance(value.get("packages"), dict):
        errors.append(f"{where}: expected an object with a packages object")
        return None
    earliest = value.get("earliest_removal")
    try:
        date.fromisoformat(earliest)
    except (TypeError, ValueError):
        errors.append(f"{where}: earliest_removal must be an ISO date")
        return None
    return value


def policy_at(ref: str, errors: list[str]) -> tuple[str | None, dict | None]:
    shown = run_git("show", f"{ref}:{POLICY_PATH}")
    if shown.returncode != 0:
        return None, None
    return shown.stdout, read_policy(shown.stdout, f"{POLICY_PATH} at {ref}", errors)


def worktree_policy(root: Path, errors: list[str]) -> tuple[str | None, dict | None]:
    try:
        raw = (root / POLICY_PATH).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, None
    except (OSError, UnicodeError) as exc:
        errors.append(f"{POLICY_PATH}: cannot read UTF-8: {exc}")
        return None, None
    return raw, read_policy(raw, POLICY_PATH, errors)


def changed_paths(merge_base: str, errors: list[str]) -> list[str]:
    diff = run_git("diff", "--name-only", "-z", merge_base, "--", "plugins")
    if diff.returncode != 0:
        errors.append(f"git diff against {merge_base} failed: {diff.stderr.strip()}")
        return []
    return [path for path in diff.stdout.split("\0") if path]


def parse_labels(raw: str, errors: list[str]) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"legacy plugin labels are invalid JSON: {exc.msg}")
        return []
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append("legacy plugin labels must be a JSON array of strings")
        return []
    return value


def package_from_path(path: str, packages: set[str]) -> str | None:
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "plugins" and parts[1] in packages:
        return parts[1]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="PR target ref")
    parser.add_argument(
        "--labels-json",
        default=os.environ.get("LEGACY_PLUGIN_LABELS", "[]"),
        help="JSON array of PR labels (default: LEGACY_PLUGIN_LABELS or [])",
    )
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="current ISO date; intended for deterministic tests",
    )
    args = parser.parse_args()

    errors: list[str] = []
    top = run_git("rev-parse", "--show-toplevel")
    if top.returncode != 0:
        print("ERROR: not inside a git repository", file=sys.stderr)
        return 1
    root = Path(top.stdout.strip())
    merged = run_git("merge-base", args.base, "HEAD")
    if merged.returncode != 0:
        print(f"ERROR: no merge base with {args.base!r}: {merged.stderr.strip()}", file=sys.stderr)
        return 1
    merge_base = merged.stdout.strip()
    paths = changed_paths(merge_base, errors)
    base_raw, base_policy = policy_at(merge_base, errors)
    head_raw, head_policy = worktree_policy(root, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if base_policy is None:
        if head_policy is None:
            print("ERROR: legacy deprecation policy is missing from both base and worktree", file=sys.stderr)
            return 1
        packages = set(head_policy["packages"])
        touched = {package_from_path(path, packages) for path in paths}
        touched.discard(None)
        missing = sorted(packages - touched)
        if missing:
            print(
                "ERROR: adopting the legacy deprecation policy must ship every package notice; "
                f"untouched: {', '.join(missing)}",
                file=sys.stderr,
            )
            return 1
        print(f"OK: adopted the frozen legacy policy for {len(packages)} packages.")
        return 0

    if not paths:
        print("OK: no changes under plugins/ relative to the PR base.")
        return 0

    labels = parse_labels(args.labels_json, errors)
    selected = [(label, LABEL_KINDS[label]) for label in labels if label in LABEL_KINDS]
    if len(selected) != 1:
        names = ", ".join(LABEL_KINDS)
        errors.append(
            "changes under plugins/ require exactly one maintainer-applied policy label: " + names
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    label, kind = selected[0]
    packages = set(base_policy["packages"])

    if kind in {"compatibility", "security"}:
        if head_policy is None or head_raw != base_raw:
            errors.append(f"{label} cannot change or remove {POLICY_PATH}")
        outside_packages = [
            path
            for path in paths
            if package_from_path(path, packages) is None and path != "plugins/README.md"
        ]
        if outside_packages:
            errors.append(
                f"{label} is package-scoped; disallowed paths: {', '.join(outside_packages)}"
            )
        touched = sorted(
            {package for path in paths if (package := package_from_path(path, packages))}
        )
        for package in touched:
            manifest = f"plugins/{package}/.claude-plugin/plugin.json"
            if manifest not in paths:
                errors.append(
                    f"plugins/{package}: {kind} fix must include a strict version bump in {manifest}"
                )
            if not (root / "plugins" / package).is_dir():
                errors.append(f"plugins/{package}: {label} cannot remove a legacy package")
        if not touched and "plugins/README.md" not in paths:
            errors.append(f"{label} did not change an existing legacy package or its policy README")
    else:
        earliest = date.fromisoformat(base_policy["earliest_removal"])
        if args.today < earliest:
            errors.append(
                f"legacy removal is blocked until {earliest.isoformat()} (today: {args.today.isoformat()})"
            )
        if (root / "plugins").exists():
            errors.append(
                "legacy removal must delete the entire plugins/ tree, including its "
                "deprecation policy and package READMEs"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {kind} exception accepted for frozen legacy plugin changes ({label}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
