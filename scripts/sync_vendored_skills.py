#!/usr/bin/env python3
"""Sync or check self-contained vendored skill references."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tempfile

from skill_catalog import (
    ROOT,
    compare_trees,
    discover_skills,
    display_path,
    symlink_errors,
)


def copy_tree_atomically(source: Path, destination: Path) -> None:
    unsafe = symlink_errors(source)
    if unsafe:
        raise ValueError("; ".join(unsafe))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        staged = temporary / destination.name
        shutil.copytree(source, staged, symlinks=True)
        staged_unsafe = symlink_errors(staged)
        if staged_unsafe:
            raise ValueError("; ".join(staged_unsafe))
        if destination.exists():
            shutil.rmtree(destination)
        staged.replace(destination)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail instead of updating drifted copies")
    args = parser.parse_args()

    skills, errors = discover_skills()
    by_name = {skill.name: skill for skill in skills}
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    for skill in skills:
        errors.extend(symlink_errors(skill.root))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    changed = 0
    for skill in skills:
        for dependency in skill.vendored_skills:
            source = by_name.get(dependency)
            if source is None:
                print(
                    f"ERROR: {display_path(skill.path)}: unknown vendored skill {dependency!r}",
                    file=sys.stderr,
                )
                return 1
            if source.vendored_skills:
                print(
                    f"ERROR: {dependency} itself vendors skills; flatten the composition first",
                    file=sys.stderr,
                )
                return 1
            destination = skill.root / "references" / dependency
            drift = compare_trees(source.root, destination)
            if not drift:
                continue
            if args.check:
                for error in drift:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            try:
                copy_tree_atomically(source.root, destination)
            except ValueError as exc:
                print(f"ERROR: refusing unsafe vendored sync: {exc}", file=sys.stderr)
                return 1
            changed += 1
            print(f"Synced {display_path(destination)} from skills/{dependency}.")

    if args.check:
        print("OK: vendored skill references match their canonical sources.")
    elif changed == 0:
        print("Vendored skill references are already up to date.")
    else:
        print(f"Updated {changed} vendored skill reference tree(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
