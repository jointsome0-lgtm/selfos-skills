#!/usr/bin/env python3
"""Build self-contained composed-skill bundles from BUNDLE.json manifests.

A composed skill declares its local dependencies once, in a machine-readable
manifest at skills/<name>/BUNDLE.json:

    {"dependencies": ["codebase-design", "grilling"]}

For every declared dependency this tool copies the complete canonical
skills/<dependency>/ tree to skills/<name>/references/<dependency>/, stamps
the copy with a GENERATED.md marker so it self-identifies as a build
artifact, removes generated trees whose declaration is gone, and maintains a
managed linguist-generated block in .gitattributes so reviews fold
regenerated trees away from authored changes.

The build is deterministic — rerunning it on unchanged sources changes
nothing — and --check reports every drifted, missing, or stale artifact
without modifying the worktree. Cycles, missing dependencies, nested
composition, and path-escaping names fail with actionable diagnostics.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tempfile

from skill_catalog import (
    BUNDLE_MANIFEST_NAME,
    GENERATED_MARKER_NAME,
    ROOT,
    Skill,
    compare_trees,
    discover_skills,
    display_path,
    load_bundle_manifest,
    symlink_errors,
)

GITATTRIBUTES_PATH = ROOT / ".gitattributes"
GITATTRIBUTES_BEGIN = "# BEGIN generated skill bundles; managed by scripts/build_bundles.py."
GITATTRIBUTES_END = "# END generated skill bundles."
REBUILD_HINT = "run python scripts/build_bundles.py to regenerate the bundles"


def render_marker(composed: Skill, dependency: Skill) -> str:
    """Deterministic self-identification stamped into every generated copy."""
    return (
        "# Generated bundle copy — do not edit\n"
        "\n"
        f"This tree is a build artifact: a byte-for-byte copy of the canonical\n"
        f"skill `skills/{dependency.name}/` (version {dependency.version}) bundled into\n"
        f"`skills/{composed.name}/` as declared by "
        f"`skills/{composed.name}/{BUNDLE_MANIFEST_NAME}`.\n"
        "\n"
        "Edit the canonical source instead, then refresh every bundle with\n"
        "`python scripts/build_bundles.py`. CI rejects drift via\n"
        "`python scripts/build_bundles.py --check`.\n"
    )


def load_bundles(skills: list[Skill]) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    bundles: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for skill in skills:
        dependencies, manifest_errors = load_bundle_manifest(skill.root)
        errors.extend(manifest_errors)
        if dependencies:
            bundles[skill.name] = dependencies
    return bundles, errors


def cycle_errors(bundles: dict[str, tuple[str, ...]]) -> list[str]:
    errors: list[str] = []
    reported: set[frozenset[str]] = set()
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dependency in bundles.get(node, ()):
            if state.get(dependency) == 1:
                cycle = stack[stack.index(dependency) :] + [dependency]
                key = frozenset(cycle)
                if key not in reported:
                    reported.add(key)
                    errors.append(
                        "dependency cycle: "
                        + " -> ".join(cycle)
                        + f"; break it by removing one edge from a {BUNDLE_MANIFEST_NAME}"
                    )
            elif state.get(dependency) != 2 and dependency in bundles:
                visit(dependency)
        stack.pop()
        state[node] = 2

    for name in sorted(bundles):
        if state.get(name) != 2:
            visit(name)
    return errors


def graph_errors(
    bundles: dict[str, tuple[str, ...]], known: dict[str, Skill]
) -> list[str]:
    errors: list[str] = []
    for name in sorted(bundles):
        where = f"skills/{name}/{BUNDLE_MANIFEST_NAME}"
        for dependency in bundles[name]:
            if dependency == name:
                errors.append(f"{where}: a skill cannot bundle itself")
                continue
            if dependency not in known:
                errors.append(
                    f"{where}: unknown dependency {dependency!r}; every dependency must "
                    "be a canonical skill folder under skills/"
                )
                continue
            if dependency in bundles and dependency != name:
                errors.append(
                    f"{where}: dependency {dependency!r} is itself a composed skill; "
                    "bundles must stay flat — inline what it needs or restructure so "
                    f"{dependency!r} has no {BUNDLE_MANIFEST_NAME}"
                )
    errors.extend(cycle_errors(bundles))
    return errors


def copy_tree_atomically(
    source: Path,
    destination: Path,
    extra_files: dict[str, bytes] | None = None,
) -> None:
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
        for name, content in sorted((extra_files or {}).items()):
            target = staged / name
            if target.exists():
                raise ValueError(
                    f"{display_path(source / name)}: canonical sources must not ship "
                    f"{name}; the name is reserved for generated bundle metadata"
                )
            target.write_bytes(content)
        if destination.exists():
            shutil.rmtree(destination)
        staged.replace(destination)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def gitattributes_lines(bundles: dict[str, tuple[str, ...]]) -> list[str]:
    return [
        f"skills/{name}/references/{dependency}/** linguist-generated=true"
        for name in sorted(bundles)
        for dependency in bundles[name]
    ]


def expected_gitattributes(existing: str, lines: list[str]) -> tuple[str | None, list[str]]:
    """Render the managed block into the existing file, appending if absent."""
    block = "\n".join([GITATTRIBUTES_BEGIN, *lines, GITATTRIBUTES_END]) + "\n"
    begin_count = existing.count(GITATTRIBUTES_BEGIN)
    end_count = existing.count(GITATTRIBUTES_END)
    if begin_count == 1 and end_count == 1:
        start = existing.index(GITATTRIBUTES_BEGIN)
        end = existing.index(GITATTRIBUTES_END)
        if end < start:
            return None, [".gitattributes managed bundle markers are out of order"]
        end += len(GITATTRIBUTES_END)
        if end < len(existing) and existing[end] == "\n":
            end += 1
        return existing[:start] + block + existing[end:], []
    if begin_count or end_count:
        return None, [".gitattributes has incomplete or duplicate managed bundle markers"]
    if not lines:
        return existing, []
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + block, []


def run(
    skills: list[Skill],
    check: bool,
    gitattributes_path: Path,
) -> tuple[int, list[str]]:
    """Build or verify every declared bundle; return (changed, diagnostics)."""
    known = {skill.name: skill for skill in skills}
    bundles, errors = load_bundles(skills)
    errors.extend(graph_errors(bundles, known))
    for skill in skills:
        errors.extend(symlink_errors(skill.root))
    if errors:
        return 0, errors

    changed = 0
    problems: list[str] = []
    for name in sorted(bundles):
        composed = known[name]
        for dependency in bundles[name]:
            source = known[dependency]
            destination = composed.root / "references" / dependency
            resolved = destination.resolve()
            if resolved.parent.parent != composed.root.resolve():
                problems.append(
                    f"skills/{name}/{BUNDLE_MANIFEST_NAME}: dependency {dependency!r} "
                    "resolves outside the composed skill folder"
                )
                continue
            marker = render_marker(composed, source)
            extra = {GENERATED_MARKER_NAME: marker.encode("utf-8")}
            drift = compare_trees(source.root, destination, extra)
            if not drift:
                continue
            if check:
                problems.extend(drift)
                problems.append(
                    f"{display_path(destination)} is stale relative to "
                    f"skills/{dependency}; {REBUILD_HINT}"
                )
                continue
            try:
                copy_tree_atomically(source.root, destination, extra)
            except ValueError as exc:
                problems.append(f"refusing unsafe bundle build: {exc}")
                continue
            changed += 1
            print(f"Built {display_path(destination)} from skills/{dependency}.")

    for skill in skills:
        references = skill.root / "references"
        if not references.is_dir():
            continue
        declared = set(bundles.get(skill.name, ()))
        for child in sorted(path for path in references.iterdir() if path.is_dir()):
            if child.name in declared:
                continue
            if not (child / GENERATED_MARKER_NAME).is_file():
                continue  # authored reference material is never touched
            if check:
                problems.append(
                    f"stale generated bundle {display_path(child)}: not declared in "
                    f"skills/{skill.name}/{BUNDLE_MANIFEST_NAME}; {REBUILD_HINT}"
                )
                continue
            shutil.rmtree(child)
            changed += 1
            print(f"Removed stale generated bundle {display_path(child)}.")

    try:
        existing = gitattributes_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = ""
    except (OSError, UnicodeError) as exc:
        problems.append(f"cannot read {gitattributes_path.name}: {exc}")
        existing = None
    if existing is not None:
        expected, attribute_errors = expected_gitattributes(
            existing, gitattributes_lines(bundles)
        )
        problems.extend(attribute_errors)
        if expected is not None and expected != existing:
            if check:
                problems.append(
                    f"{gitattributes_path.name} managed bundle block is stale; {REBUILD_HINT}"
                )
            else:
                gitattributes_path.write_text(expected, encoding="utf-8")
                changed += 1
                print(f"Wrote the managed bundle block to {gitattributes_path.name}.")

    return changed, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail instead of updating stale artifacts"
    )
    args = parser.parse_args()

    skills, errors = discover_skills()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    changed, problems = run(skills, args.check, GITATTRIBUTES_PATH)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    if args.check:
        print("OK: generated skill bundles match their canonical sources.")
    elif changed == 0:
        print("Generated skill bundles are already up to date.")
    else:
        print(f"Updated {changed} generated bundle artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
