#!/usr/bin/env python3
"""Shared parser and helpers for the canonical Agent Skills catalog."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import json
from pathlib import Path
import re
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
METADATA_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
THIRD_PERSON_RE = re.compile(r"^(?:Does|Has|Is|[A-Z][A-Za-z'-]*s)\b")
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
    # Documented host-specific exception (README "intentionally host-specific"
    # surface): Claude Code only honors this guard as a top-level field, other
    # hosts ignore it, and the prose explicit-request contract stays canonical.
    "disable-model-invocation",
}
RUNTIME_SUFFIX_REQUIREMENTS = {
    ".py": "python",
    ".sh": "bash",
}


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    root: Path
    fields: dict[str, str]
    metadata: dict[str, str]
    body: str

    @property
    def explicit_only(self) -> bool:
        return self.metadata.get("selfos.explicit-only", "false").casefold() == "true"

    @property
    def version(self) -> str | None:
        return self.metadata.get("selfos.version")

    @property
    def vendored_skills(self) -> tuple[str, ...]:
        raw = self.metadata.get("selfos.vendored-skills", "")
        return tuple(part.strip() for part in raw.split(",") if part.strip())


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def parse_scalar(raw: str, path: Path, line_number: int) -> tuple[str | None, list[str]]:
    """Parse the strict single-line scalar subset used by this repository."""

    def checked(value: str) -> tuple[str | None, list[str]]:
        if CONTROL_RE.search(value):
            return None, [
                f"{display_path(path)}:{line_number}: frontmatter values must not contain control characters"
            ]
        return value, []

    value = raw.strip()
    if not value:
        return None, [f"{display_path(path)}:{line_number}: frontmatter value must not be empty"]
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            return None, [
                f"{display_path(path)}:{line_number}: invalid double-quoted value: {exc.msg}"
            ]
        if not isinstance(parsed, str):
            return None, [f"{display_path(path)}:{line_number}: frontmatter values must be strings"]
        return checked(parsed)
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            return None, [f"{display_path(path)}:{line_number}: unterminated single-quoted value"]
        inner = value[1:-1]
        parsed_characters: list[str] = []
        index = 0
        while index < len(inner):
            if inner[index] != "'":
                parsed_characters.append(inner[index])
                index += 1
                continue
            if index + 1 >= len(inner) or inner[index + 1] != "'":
                return None, [
                    f"{display_path(path)}:{line_number}: apostrophes in single-quoted frontmatter must be doubled"
                ]
            parsed_characters.append("'")
            index += 2
        return checked("".join(parsed_characters))
    if value[0] in "|>":
        return None, [
            f"{display_path(path)}:{line_number}: folded and multiline frontmatter values are not supported"
        ]
    return checked(value)


def parse_skill_text(text: str, path: Path) -> tuple[Skill | None, list[str]]:
    """Parse one SKILL.md string using path only for diagnostics and identity."""
    errors: list[str] = []
    relative = display_path(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [f"{relative}:1: SKILL.md must start with ---"]
    try:
        closing = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return None, [f"{relative}: frontmatter is missing its closing ---"]

    fields: dict[str, str] = {}
    metadata: dict[str, str] = {}
    index = 1
    while index < closing:
        line = lines[index]
        line_number = index + 1
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[:1].isspace():
            errors.append(f"{relative}:{line_number}: unexpected indentation in frontmatter")
            index += 1
            continue
        key, separator, raw_value = line.partition(":")
        key = key.strip()
        if not separator or not FIELD_RE.fullmatch(key):
            errors.append(f"{relative}:{line_number}: malformed frontmatter field; expected key: value")
            index += 1
            continue
        if key in fields or (key == "metadata" and metadata):
            errors.append(f"{relative}:{line_number}: duplicate frontmatter field {key!r}")
            index += 1
            continue
        if key == "metadata":
            if raw_value.strip():
                errors.append(f"{relative}:{line_number}: metadata must be an indented string map")
            fields[key] = ""
            index += 1
            while index < closing:
                child = lines[index]
                child_number = index + 1
                if not child.strip() or child.lstrip().startswith("#"):
                    index += 1
                    continue
                if not child.startswith("  ") or child.startswith("   "):
                    break
                child_key, child_sep, child_raw = child[2:].partition(":")
                child_key = child_key.strip()
                if not child_sep or not METADATA_KEY_RE.fullmatch(child_key):
                    errors.append(
                        f"{relative}:{child_number}: metadata entries must be two-space-indented key: value pairs"
                    )
                    index += 1
                    continue
                if child_key in metadata:
                    errors.append(f"{relative}:{child_number}: duplicate metadata key {child_key!r}")
                    index += 1
                    continue
                parsed, scalar_errors = parse_scalar(child_raw, path, child_number)
                errors.extend(scalar_errors)
                if parsed is not None:
                    metadata[child_key] = parsed
                index += 1
            continue
        parsed, scalar_errors = parse_scalar(raw_value, path, line_number)
        errors.extend(scalar_errors)
        if parsed is not None:
            fields[key] = parsed
        index += 1

    for required in ("name", "description"):
        if required not in fields:
            errors.append(f"{relative}: frontmatter is missing required field {required!r}")
    if "name" not in fields or "description" not in fields:
        return None, errors

    body = "\n".join(lines[closing + 1 :]).strip()
    skill = Skill(
        name=fields["name"],
        description=fields["description"],
        path=path,
        root=path.parent,
        fields=fields,
        metadata=metadata,
        body=body,
    )
    return skill, errors


def parse_skill(path: Path) -> tuple[Skill | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [f"{display_path(path)}: cannot read UTF-8 skill file: {exc}"]
    return parse_skill_text(text, path)


def parse_semver(version: str) -> tuple[int, int, int] | None:
    match = SEMVER_RE.fullmatch(version)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def version_errors(skill: Skill) -> list[str]:
    relative = display_path(skill.path)
    version = skill.version
    if version is None:
        return [f"{relative}: metadata.selfos.version is required"]
    parsed = parse_semver(version)
    if parsed is None:
        return [
            f"{relative}: metadata.selfos.version must be semantic X.Y.Z "
            "with no leading zeroes"
        ]
    if parsed == (0, 0, 0):
        return [f"{relative}: metadata.selfos.version must be greater than 0.0.0"]
    return []


def derive_adapter_version(skills: Iterable[Skill]) -> tuple[str | None, list[str]]:
    """Derive a monotonic aggregate SemVer from canonical per-skill versions."""
    totals = [0, 0, 0]
    errors: list[str] = []
    for skill in skills:
        declared_errors = version_errors(skill)
        errors.extend(declared_errors)
        if declared_errors:
            continue
        assert skill.version is not None
        parsed = parse_semver(skill.version)
        assert parsed is not None
        for index, component in enumerate(parsed):
            totals[index] += component
    if errors:
        return None, errors
    return ".".join(str(component) for component in totals), []


def discover_skills() -> tuple[list[Skill], list[str]]:
    paths = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
    if not paths:
        return [], ["no canonical skills found under skills/<name>/SKILL.md"]
    skills: list[Skill] = []
    errors: list[str] = []
    for path in paths:
        unsafe = next(
            (candidate for candidate in (path.parent, path) if candidate.is_symlink()),
            None,
        )
        if unsafe is not None:
            errors.append(f"{display_path(unsafe)}: skill trees must not contain symlinks")
            continue
        skill, parse_errors = parse_skill(path)
        errors.extend(parse_errors)
        if skill is not None:
            skills.append(skill)
    return sorted(skills, key=lambda item: item.name), errors


def source_files(root: Path) -> dict[Path, Path]:
    """Return portable files below root, keyed by relative path."""
    ignored_names = {".DS_Store"}
    result: dict[Path, Path] = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.name in ignored_names or "__pycache__" in path.parts:
            continue
        result[path.relative_to(root)] = path
    return result


def compatibility_errors(skill: Skill) -> list[str]:
    """Check declared compatibility against executable files shipped by a skill."""
    relative = display_path(skill.path)
    compatibility = skill.fields.get("compatibility")
    if compatibility is None:
        return [f"{relative}: frontmatter is missing required field 'compatibility'"]

    normalized = compatibility.casefold()
    errors: list[str] = []
    files = source_files(skill.root)
    for suffix, runtime in RUNTIME_SUFFIX_REQUIREMENTS.items():
        matching = sorted(path.as_posix() for path in files if path.suffix.casefold() == suffix)
        if matching and runtime not in normalized:
            examples = ", ".join(matching[:3])
            if len(matching) > 3:
                examples += ", …"
            errors.append(
                f"{relative}: compatibility must declare {runtime} because the skill ships "
                f"{suffix} files ({examples})"
            )
    return errors


def symlinks_in_tree(root: Path) -> list[Path]:
    """Return symlinks without following them, including a symlinked root."""
    if root.is_symlink():
        return [root]
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.is_symlink())


def symlink_errors(root: Path) -> list[str]:
    return [
        f"{display_path(path)}: skill trees must not contain symlinks"
        for path in symlinks_in_tree(root)
    ]


def compare_trees(source: Path, destination: Path) -> list[str]:
    errors = symlink_errors(source) + symlink_errors(destination)
    if errors:
        return errors
    source_map = source_files(source)
    destination_map = source_files(destination) if destination.is_dir() else {}
    source_names = set(source_map)
    destination_names = set(destination_map)
    for missing in sorted(source_names - destination_names):
        errors.append(f"missing vendored file {display_path(destination / missing)}")
    for extra in sorted(destination_names - source_names):
        errors.append(f"unexpected vendored file {display_path(destination / extra)}")
    for relative in sorted(source_names & destination_names):
        try:
            source_bytes = source_map[relative].read_bytes()
            destination_bytes = destination_map[relative].read_bytes()
        except OSError as exc:
            errors.append(f"cannot compare vendored file {relative.as_posix()}: {exc}")
            continue
        if source_bytes != destination_bytes:
            errors.append(
                f"vendored file drift: {display_path(destination / relative)} != "
                f"{display_path(source / relative)}"
            )
    return errors


def iter_vendored_edges(skills: Iterable[Skill]) -> Iterable[tuple[Skill, str]]:
    for skill in skills:
        for dependency in skill.vendored_skills:
            yield skill, dependency


SHA_RE = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
NO_VENDOR_MARKER = "No vendored content."
DELEGATION_HEADING = "Bundled reference provenance"
DELEGATION_RE = re.compile(
    r"(?m)^- `references/([a-z0-9]+(?:-[a-z0-9]+)*)/PROVENANCE\.md`$"
)


def check_pin(chunk: str, where: str, errors: list[str]) -> None:
    labeled = re.findall(r"(?i)\b(?:blob|commit|merge)\b[^\r\n]*?\b([0-9a-f]{40})\b", chunk)
    if not labeled:
        errors.append(
            f"{where}: must pin upstream content to a labeled 40-hex SHA (blob/commit/merge …)"
        )
    if "0" * 40 in SHA_RE.findall(chunk):
        errors.append(f"{where}: pins must be real SHAs, not the all-zero placeholder")


def check_import_date(chunk: str, where: str, errors: list[str]) -> None:
    imported = re.search(r"\bImported\b", chunk)
    date_valid = False
    if imported is not None:
        for match in DATE_RE.finditer(chunk[imported.end():]):
            try:
                datetime.date(*(int(group) for group in match.groups()))
            except ValueError:
                continue
            date_valid = True
            break
    if not date_valid:
        errors.append(f"{where}: must record a real import date (Imported … YYYY-MM-DD)")


def validate_provenance(
    package_root: Path,
    errors: list[str],
    vendored_skills: Iterable[str] = (),
) -> None:
    """Every "##" section is a vendored item carrying its own labeled pin and
    import date, so one pinned section cannot vouch for another; the sole
    exemption is the license notice — a slash-free heading naming "license" —
    checked file-wide because one upstream's notice may cover several
    sections. Presence-and-shape checks against forgetting, not cryptographic
    verification.
    """
    dependencies = tuple(vendored_skills)
    path = package_root / "PROVENANCE.md"
    where = display_path(path)
    if path.is_symlink():
        errors.append(f"{where}: must be a regular file, not a symlink")
        return
    if not path.exists():
        errors.append(f"{where}: missing; pin vendored sources or state {NO_VENDOR_MARKER!r}")
        return
    try:
        if path.stat().st_size > 64 * 1024:
            errors.append(f"{where}: implausibly large (over 64 KiB)")
            return
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{where}: cannot read UTF-8: {exc}")
        return

    if NO_VENDOR_MARKER in text:
        statements = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if len(statements) == 1 and statements[0].startswith(NO_VENDOR_MARKER):
            if dependencies:
                errors.append(
                    f"{where}: {NO_VENDOR_MARKER!r} is false for a composed skill; "
                    f"delegate every bundled reference under '## {DELEGATION_HEADING}'"
                )
            return
        errors.append(
            f"{where}: {NO_VENDOR_MARKER!r} must open the file's only statement besides "
            f"headings; with vendored sections present, drop the marker and pin them"
        )

    delegation_headings = text.splitlines().count(f"## {DELEGATION_HEADING}")
    delegated = DELEGATION_RE.findall(text)
    expected_delegations = set(dependencies)
    actual_delegations = set(delegated)
    if dependencies:
        if delegation_headings != 1:
            errors.append(
                f"{where}: composed skills must contain exactly one "
                f"'## {DELEGATION_HEADING}' section"
            )
        if len(delegated) != len(actual_delegations):
            errors.append(f"{where}: bundled reference provenance entries must not repeat")
        for dependency in sorted(expected_delegations - actual_delegations):
            errors.append(
                f"{where}: missing bundled provenance delegation "
                f"'references/{dependency}/PROVENANCE.md'"
            )
        for dependency in sorted(actual_delegations - expected_delegations):
            errors.append(
                f"{where}: undeclared bundled provenance delegation "
                f"'references/{dependency}/PROVENANCE.md'"
            )
        for dependency in dependencies:
            delegated_path = package_root / "references" / dependency / "PROVENANCE.md"
            if not delegated_path.is_file():
                errors.append(
                    f"{where}: delegated provenance file is missing: "
                    f"references/{dependency}/PROVENANCE.md"
                )
    elif delegation_headings or delegated:
        errors.append(
            f"{where}: bundled provenance delegation requires selfos.vendored-skills"
        )

    sections: list[tuple[str, str]] = []
    for chunk in re.split(r"(?m)^## +", text)[1:]:
        heading, _, body = chunk.partition("\n")
        heading = heading.strip()
        if heading == DELEGATION_HEADING:
            continue
        if "license" in heading.lower() and "/" not in heading:
            continue
        sections.append((heading, body))

    if sections:
        for heading, body in sections:
            section_where = f"{where}: section {heading!r}"
            check_pin(body, section_where, errors)
            check_import_date(body, section_where, errors)
    elif not dependencies:
        check_pin(text, where, errors)
        check_import_date(text, where, errors)

    if not sections and dependencies:
        return

    notice_complete = (
        re.search(r"Copyright \(c\) \d{4}", text, re.IGNORECASE)
        and "Permission is hereby granted" in text
        and "The above copyright notice and this permission notice" in text
        and 'THE SOFTWARE IS PROVIDED "AS IS"' in text
    )
    if not notice_complete:
        errors.append(
            f"{where}: must carry the full upstream license notice "
            f"(copyright line, permission grant, notice condition, warranty disclaimer)"
        )
