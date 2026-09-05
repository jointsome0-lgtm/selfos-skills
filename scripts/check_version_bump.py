#!/usr/bin/env python3
"""Require canonical skill bumps and validate generated adapter versions.

Diffs the worktree against the merge base with --base (the PR target in CI).
Every changed tree below skills/<name>/ must strictly increase that skill's
metadata.selfos.version in canonical SKILL.md. A bump-only diff passes. New
skills pass with any valid non-zero version. Removing a skill is allowed
only as a whole-tree removal whose derived adapter version still strictly
increases: fold the removed skill's components into VERSION_BASE.json.

Both aggregate host manifest versions are the committed VERSION_BASE.json
offset plus the component-wise sum of all canonical skill versions. The gate
validates that derived value even when a manifest was not touched, so stale
generated adapters cannot pass CI, and it may never decrease relative to the
merge base — strictly increasing whenever a skill is removed or
VERSION_BASE.json changes.
Generated version-only manifest edits are exempt from separate guarding;
other aggregate adapter or marketplace edits require packaging bumps across
the full canonical catalog so host caches also see those changes.

Operates on the git repository containing the current directory, so it works
in any checkout and in the self-test's invented fixture repositories.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from skill_catalog import (
    VERSION_BASE_NAME,
    Skill,
    derive_adapter_version,
    parse_semver,
    parse_skill,
    parse_skill_text,
    version_errors,
)

DEFAULT_BASES = ("origin/main", "main")
ADAPTER_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
)
ADAPTER_ROOTS = (".claude-plugin/", ".codex-plugin/", ".agents/")


def run_git(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *argv], capture_output=True, text=True)


def resolve_ref(ref: str) -> bool:
    return run_git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def parse_manifest_version(raw: str, where: str, errors: list[str]) -> str | None:
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


def manifest_version_at(ref: str, manifest_path: str, errors: list[str]) -> str | None:
    shown = run_git("show", f"{ref}:{manifest_path}")
    if shown.returncode != 0:
        return None
    return parse_manifest_version(shown.stdout, f"{manifest_path} at {ref}", errors)


def manifest_version_in_worktree(
    root: Path, manifest_path: str, errors: list[str]
) -> str | None:
    try:
        raw = (root / manifest_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as exc:
        errors.append(f"{manifest_path}: cannot read UTF-8 file: {exc}")
        return None
    return parse_manifest_version(raw, manifest_path, errors)


def changed_paths(merge_base: str, errors: list[str]) -> list[str] | None:
    diff = run_git("diff", "--name-only", "-z", merge_base, "--")
    if diff.returncode != 0:
        errors.append(f"git diff against {merge_base} failed: {diff.stderr.strip()}")
        return None
    return [path for path in diff.stdout.split("\0") if path]


def manifest_payload_without_version(raw: str) -> object:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    payload = dict(value)
    payload.pop("version", None)
    return payload


def substantive_adapter_changes(
    root: Path,
    merge_base: str,
    paths: list[str],
) -> list[str]:
    """Ignore generated manifest-version-only edits; return other adapter edits."""
    changed: list[str] = []
    for path in paths:
        if not path.startswith(ADAPTER_ROOTS):
            continue
        if path not in ADAPTER_MANIFESTS:
            changed.append(path)
            continue
        base = run_git("show", f"{merge_base}:{path}")
        try:
            head_raw = (root / path).read_text(encoding="utf-8")
            if base.returncode != 0 or (
                manifest_payload_without_version(base.stdout)
                != manifest_payload_without_version(head_raw)
            ):
                changed.append(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            # The normal manifest validators report the detailed parse error.
            changed.append(path)
    return changed


def parsed_skill_from_text(
    raw: str,
    label: str,
    errors: list[str],
    *,
    require_version: bool,
) -> Skill | None:
    skill, parse_errors = parse_skill_text(raw, Path(label))
    errors.extend(parse_errors)
    if skill is None:
        return None
    if require_version:
        errors.extend(version_errors(skill))
    elif skill.version is not None and parse_semver(skill.version) is None:
        errors.append(
            f"{label}: metadata.selfos.version must be semantic X.Y.Z with no leading zeroes"
        )
    return skill


def check_canonical_skill(
    root: Path,
    merge_base: str,
    name: str,
    errors: list[str],
    removed: list[str],
) -> bool:
    skill_path = f"skills/{name}/SKILL.md"
    shown = run_git("show", f"{merge_base}:{skill_path}")
    base_exists = shown.returncode == 0

    try:
        head_raw = (root / skill_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        if not base_exists:
            errors.append(f"skills/{name}: changed tree has no canonical SKILL.md")
        elif (root / "skills" / name).exists():
            errors.append(
                f"skills/{name}: canonical SKILL.md was removed but other files remain; "
                "remove the whole skill tree or restore a bumped SKILL.md"
            )
        else:
            removed.append(name)
        return False
    except (OSError, UnicodeError) as exc:
        errors.append(f"{skill_path}: cannot read UTF-8 file: {exc}")
        return False

    head = parsed_skill_from_text(head_raw, skill_path, errors, require_version=True)
    if head is None or head.version is None:
        return False
    head_semver = parse_semver(head.version)
    if head_semver is None or head_semver == (0, 0, 0):
        return False

    if not base_exists:
        return True

    base = parsed_skill_from_text(
        shown.stdout,
        f"{skill_path} at {merge_base}",
        errors,
        require_version=False,
    )
    if base is None:
        return False
    if base.version is None:
        return True  # one-time adoption of canonical versions
    base_semver = parse_semver(base.version)
    if base_semver is None:
        return False
    if head_semver == base_semver:
        errors.append(
            f"skills/{name}: tree changed but metadata.selfos.version stayed at "
            f"{head.version!r}; bump {skill_path}"
        )
    elif head_semver < base_semver:
        errors.append(
            f"skills/{name}: metadata.selfos.version decreased from {base.version!r} "
            f"to {head.version!r}; canonical skill versions must increase"
        )
    return True


def discover_worktree_skills(root: Path, errors: list[str]) -> list[Skill]:
    skills: list[Skill] = []
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        skill, parse_errors = parse_skill(path)
        errors.extend(parse_errors)
        if skill is None:
            continue
        errors.extend(version_errors(skill))
        skills.append(skill)
    if (root / "skills").is_dir() and not skills:
        errors.append("no canonical skills found under skills/<name>/SKILL.md")
    return skills


def check_derived_adapters(root: Path, errors: list[str]) -> str | None:
    if not (root / "skills").is_dir():
        return None
    skills = discover_worktree_skills(root, errors)
    expected, derivation_errors = derive_adapter_version(skills, root)
    # discover_worktree_skills already reports the same per-skill errors.
    if derivation_errors or expected is None:
        return None
    for manifest_path in ADAPTER_MANIFESTS:
        actual = manifest_version_in_worktree(root, manifest_path, errors)
        if actual is None:
            errors.append(f"{manifest_path}: required generated adapter manifest is missing")
        elif actual != expected:
            errors.append(
                f"{manifest_path}: derived version is stale: found {actual!r}, "
                f"expected {expected!r} from canonical skill versions; "
                "run python scripts/build_index.py"
            )
    return expected


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
    canonical: list[str] = []
    removed: list[str] = []
    adapter_changes: list[str] = []
    if paths is not None:
        canonical = sorted(
            {
                parts[1]
                for path in paths
                if len(parts := path.split("/")) >= 3 and parts[0] == "skills"
            }
        )
        adapter_changes = substantive_adapter_changes(root, merge_base, paths)
        for name in canonical:
            check_canonical_skill(root, merge_base, name, errors, removed)

        if adapter_changes:
            catalog_names = sorted(path.parent.name for path in (root / "skills").glob("*/SKILL.md"))
            missing_packaging_bumps = sorted(set(catalog_names) - set(canonical))
            if missing_packaging_bumps:
                examples = ", ".join(adapter_changes[:3])
                if len(adapter_changes) > 3:
                    examples += ", …"
                errors.append(
                    f"aggregate adapter content changed ({examples}) without bundle-wide "
                    "canonical packaging bumps; bump every skills/<name>/SKILL.md version "
                    f"(missing: {', '.join(missing_packaging_bumps)})"
                )

    adapter_version = check_derived_adapters(root, errors)

    if paths is not None and adapter_version is not None:
        base_version = manifest_version_at(merge_base, ADAPTER_MANIFESTS[0], errors)
        base_semver = parse_semver(base_version) if base_version is not None else None
        head_semver = parse_semver(adapter_version)
        if base_semver is not None and head_semver is not None:
            if head_semver < base_semver:
                errors.append(
                    f"derived adapter version decreased from {base_version!r} to "
                    f"{adapter_version!r}; it must never decrease and must strictly "
                    "increase when skills are removed; raise VERSION_BASE.json "
                    "instead of lowering it"
                )
            elif head_semver == base_semver and (removed or VERSION_BASE_NAME in paths):
                errors.append(
                    f"skill removal or a {VERSION_BASE_NAME} change must strictly "
                    "increase the derived adapter version, but it stayed at "
                    f"{adapter_version!r}; fold at least a patch into {VERSION_BASE_NAME}"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not canonical:
        suffix = (
            f"; generated adapter version {adapter_version} is current"
            if adapter_version is not None
            else ""
        )
        print(f"OK: no guarded content changes relative to {base}{suffix}.")
    else:
        adapter = (
            f"; generated adapter version {adapter_version} is current"
            if adapter_version is not None
            else ""
        )
        print(
            f"OK: {len(canonical)} changed canonical skill(s) relative to {base}; "
            f"{len(adapter_changes)} substantive adapter change(s){adapter}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
