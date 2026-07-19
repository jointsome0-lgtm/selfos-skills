#!/usr/bin/env python3
"""Validate the legacy Claude domain packages and aggregate marketplace entry."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import sys

from skill_catalog import CONTROL_RE, parse_semver, validate_provenance

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS = ROOT / "plugins"
DEPRECATION = PLUGINS / "deprecation.json"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^ {0,3}(?:`{3,}|~{3,})")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_object(path: Path, errors: list[str]) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{relative(path)}: missing")
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{relative(path)}: invalid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{relative(path)}: top-level value must be an object")
        return None
    return value


def required_text(data: dict, key: str, where: str, errors: list[str]) -> str | None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: {key!r} must be non-empty text")
        return None
    if CONTROL_RE.search(value):
        errors.append(f"{where}: {key!r} must not contain control characters")
        return None
    return value


def validate_manifest(name: str, package_root: Path, errors: list[str]) -> None:
    path = package_root / ".claude-plugin" / "plugin.json"
    manifest = load_object(path, errors)
    if manifest is None:
        return
    where = relative(path)
    manifest_name = required_text(manifest, "name", where, errors)
    version = required_text(manifest, "version", where, errors)
    required_text(manifest, "description", where, errors)
    if manifest_name is not None and manifest_name != name:
        errors.append(f"{where}: name {manifest_name!r} must match {name!r}")
    if version is not None and not VERSION_RE.fullmatch(version):
        errors.append(f"{where}: version must be MAJOR.MINOR.PATCH")


def migration_command(source: str, skills: list[str]) -> str:
    selected = " ".join(skills)
    return (
        f"npx skills add {source} --skill {selected} "
        "--agent claude-code --global --yes"
    )


def load_deprecation(errors: list[str], *, required: bool = True) -> dict | None:
    if not DEPRECATION.is_file():
        if required:
            errors.append(f"{relative(DEPRECATION)}: missing")
        return None
    policy = load_object(DEPRECATION, errors)
    if policy is None:
        return None
    where = relative(DEPRECATION)
    if policy.get("schema_version") != 1:
        errors.append(f"{where}: schema_version must be 1")
    for key in ("deprecated_on", "earliest_removal"):
        value = required_text(policy, key, where, errors)
        if value is not None:
            try:
                date.fromisoformat(value)
            except ValueError:
                errors.append(f"{where}: {key} must be an ISO date")
    required_text(policy, "removal_issue", where, errors)
    required_text(policy, "canonical_source", where, errors)
    packages = policy.get("packages")
    if not isinstance(packages, dict) or not packages:
        errors.append(f"{where}: packages must be a non-empty object")
    return policy


def validate_deprecation_notice(
    name: str, package_root: Path, policy: dict, errors: list[str]
) -> None:
    packages = policy.get("packages")
    package_policy = packages.get(name) if isinstance(packages, dict) else None
    if not isinstance(package_policy, dict):
        return
    where = f"{relative(DEPRECATION)}: packages.{name}"
    deprecation_version = required_text(
        package_policy, "deprecation_version", where, errors
    )
    skills = package_policy.get("canonical_skills")
    if (
        not isinstance(skills, list)
        or not skills
        or any(not isinstance(skill, str) or not NAME_RE.fullmatch(skill) for skill in skills)
        or len(skills) != len(set(skills))
    ):
        errors.append(f"{where}: canonical_skills must be unique kebab-case names")
        return
    for skill in skills:
        if not (ROOT / "skills" / skill / "SKILL.md").is_file():
            errors.append(f"{where}: canonical skill {skill!r} does not exist")

    source = policy.get("canonical_source")
    earliest = policy.get("earliest_removal")
    issue = policy.get("removal_issue")
    if not all(isinstance(value, str) for value in (source, earliest, issue)):
        return
    command = migration_command(source, skills)
    issue_number = issue.rstrip("/").rsplit("/", 1)[-1]

    manifest_path = package_root / ".claude-plugin" / "plugin.json"
    manifest = load_object(manifest_path, errors)
    if manifest is not None:
        description = manifest.get("description")
        version = manifest.get("version")
        if not isinstance(description, str) or not all(
            token in description
            for token in (
                "DEPRECATED:",
                command,
                earliest,
                "downstream migration",
                "install smoke checks",
                f"issue #{issue_number}",
            )
        ):
            errors.append(
                f"{relative(manifest_path)}: description must carry the complete deprecation notice"
            )
        baseline = parse_semver(deprecation_version) if deprecation_version else None
        current = parse_semver(version) if isinstance(version, str) else None
        if baseline is None:
            errors.append(f"{where}: deprecation_version must be semantic X.Y.Z")
        elif current is not None and current < baseline:
            errors.append(
                f"{relative(manifest_path)}: version {version!r} predates the "
                f"deprecation release {deprecation_version!r}"
            )

    readme_path = package_root / "README.md"
    try:
        readme = readme_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeError) as exc:
        errors.append(f"{relative(readme_path)}: missing or unreadable deprecation README: {exc}")
        return
    required = (
        f"`{name}@selfos` is deprecated",
        deprecation_version or "",
        command,
        f"/plugin update {name}@selfos",
        f"/plugin uninstall {name}@selfos",
        earliest,
        issue,
        "downstream repositories",
        "installation smoke matrix",
        "major-migration release note",
    )
    missing = [token for token in required if token not in readme]
    if missing:
        errors.append(
            f"{relative(readme_path)}: incomplete deprecation notice; missing {missing!r}"
        )


def validate_links(errors: list[str]) -> None:
    repository_root = ROOT.resolve()
    for path in sorted(PLUGINS.glob("**/*.md")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative(path)}: cannot read UTF-8: {exc}")
            continue
        fenced = False
        for line_number, line in enumerate(lines, start=1):
            if FENCE_RE.match(line):
                fenced = not fenced
                continue
            if fenced:
                continue
            for target in LINK_RE.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#", 1)[0]
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"{relative(path)}:{line_number}: missing link target {target!r}")
                elif repository_root != resolved and repository_root not in resolved.parents:
                    errors.append(f"{relative(path)}:{line_number}: link target escapes repository")


def main() -> int:
    errors: list[str] = []
    # A completed removal has no plugins/ tree or deprecation policy. Legacy
    # marketplace entries below make the policy mandatory while any remain.
    deprecation = load_deprecation(errors, required=False)
    marketplace = load_object(MARKETPLACE, errors)
    registered: set[Path] = set()
    legacy_count = 0
    aggregate_count = 0
    if marketplace is not None:
        where = relative(MARKETPLACE)
        marketplace_name = required_text(marketplace, "name", where, errors)
        if marketplace_name is not None and not NAME_RE.fullmatch(marketplace_name):
            errors.append(f"{where}: marketplace name {marketplace_name!r} must be kebab-case")
        owner = marketplace.get("owner")
        if not isinstance(owner, dict):
            errors.append(f"{where}: owner must be an object")
        else:
            required_text(owner, "name", f"{where}: owner", errors)
        entries = marketplace.get("plugins")
        if not isinstance(entries, list) or not entries:
            errors.append(f"{where}: plugins must be a non-empty list")
            entries = []
        seen: set[str] = set()
        for index, entry in enumerate(entries):
            item_where = f"{where}: plugins[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{item_where}: must be an object")
                continue
            name = required_text(entry, "name", item_where, errors)
            source = required_text(entry, "source", item_where, errors)
            required_text(entry, "description", item_where, errors)
            if name is None or source is None:
                continue
            if not NAME_RE.fullmatch(name):
                errors.append(f"{item_where}: invalid kebab-case name {name!r}")
            if name in seen:
                errors.append(f"{item_where}: duplicate plugin name {name!r}")
            seen.add(name)
            if source == "./":
                aggregate_count += 1
                if name != "selfos-skills":
                    errors.append(f"{item_where}: root aggregate must be named 'selfos-skills'")
                validate_manifest(name, ROOT, errors)
                continue
            if not source.startswith("./plugins/"):
                errors.append(f"{item_where}: legacy source must point into ./plugins/")
                continue
            package = (ROOT / source).resolve()
            if package.parent != PLUGINS.resolve() or package.name != name or not package.is_dir():
                errors.append(f"{item_where}: source must be the matching direct child of ./plugins/")
                continue
            registered.add(package)
            legacy_count += 1
            validate_manifest(name, package, errors)
            validate_provenance(package, errors)
            if deprecation is not None:
                validate_deprecation_notice(name, package, deprecation, errors)

    if aggregate_count != 1:
        errors.append("Claude marketplace must contain exactly one root selfos-skills aggregate entry")
    if legacy_count and deprecation is None:
        errors.append(
            f"{relative(DEPRECATION)}: required while legacy marketplace packages remain"
        )
    if deprecation is not None:
        packages = deprecation.get("packages")
        if isinstance(packages, dict):
            registered_names = {path.name for path in registered}
            declared_names = set(packages)
            if registered_names != declared_names:
                errors.append(
                    f"{relative(DEPRECATION)}: package set differs from the legacy marketplace; "
                    f"declared={sorted(declared_names)!r}, registered={sorted(registered_names)!r}"
                )
        root_readme = PLUGINS / "README.md"
        try:
            root_notice = root_readme.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative(root_readme)}: cannot read UTF-8: {exc}")
        else:
            tokens = (
                deprecation.get("deprecated_on"),
                deprecation.get("earliest_removal"),
                deprecation.get("removal_issue"),
                "npx skills add jointsome0-lgtm/selfos-skills",
                "legacy-plugin-compatibility",
                "legacy-plugin-security",
                "legacy-plugin-removal",
            )
            if any(not isinstance(token, str) or token not in root_notice for token in tokens):
                errors.append(f"{relative(root_readme)}: incomplete root deprecation policy")
    if PLUGINS.is_dir():
        for child in sorted(PLUGINS.iterdir()):
            if child.is_dir() and child.resolve() not in registered:
                errors.append(f"{relative(child)}: legacy package is not registered in the marketplace")
        validate_links(errors)
    elif deprecation is not None or legacy_count:
        errors.append("plugins/: missing while legacy package metadata remains")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: validated aggregate Claude adapter and {legacy_count} legacy packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
