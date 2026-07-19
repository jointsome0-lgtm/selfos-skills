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
    "disable-model-invocation",
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
        return checked(value[1:-1].replace("''", "'"))
    if value[0] in "|>":
        return None, [
            f"{display_path(path)}:{line_number}: folded and multiline frontmatter values are not supported"
        ]
    return checked(value)


def parse_skill(path: Path) -> tuple[Skill | None, list[str]]:
    errors: list[str] = []
    relative = display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [f"{relative}: cannot read UTF-8 skill file: {exc}"]
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


def discover_skills() -> tuple[list[Skill], list[str]]:
    paths = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
    if not paths:
        return [], ["no canonical skills found under skills/<name>/SKILL.md"]
    skills: list[Skill] = []
    errors: list[str] = []
    for path in paths:
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


def compare_trees(source: Path, destination: Path) -> list[str]:
    errors: list[str] = []
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


def validate_provenance(package_root: Path, errors: list[str]) -> None:
    """Every "##" section is a vendored item carrying its own labeled pin and
    import date, so one pinned section cannot vouch for another; the sole
    exemption is the license notice — a slash-free heading naming "license" —
    checked file-wide because one upstream's notice may cover several
    sections. Presence-and-shape checks against forgetting, not cryptographic
    verification.
    """
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
            return
        errors.append(
            f"{where}: {NO_VENDOR_MARKER!r} must open the file's only statement besides "
            f"headings; with vendored sections present, drop the marker and pin them"
        )

    sections: list[tuple[str, str]] = []
    for chunk in re.split(r"(?m)^## +", text)[1:]:
        heading, _, body = chunk.partition("\n")
        heading = heading.strip()
        if "license" in heading.lower() and "/" not in heading:
            continue
        sections.append((heading, body))

    if sections:
        for heading, body in sections:
            section_where = f"{where}: section {heading!r}"
            check_pin(body, section_where, errors)
            check_import_date(body, section_where, errors)
    else:
        check_pin(text, where, errors)
        check_import_date(text, where, errors)

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
