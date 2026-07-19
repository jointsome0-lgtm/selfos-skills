#!/usr/bin/env python3
"""Validate the legacy Claude domain packages and aggregate marketplace entry."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS = ROOT / "plugins"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
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
                dt.date(*(int(group) for group in match.groups()))
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
    where = relative(path)
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
    marketplace = load_object(MARKETPLACE, errors)
    registered: set[Path] = set()
    legacy_count = 0
    aggregate_count = 0
    if marketplace is not None:
        where = relative(MARKETPLACE)
        required_text(marketplace, "name", where, errors)
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

    if aggregate_count != 1:
        errors.append("Claude marketplace must contain exactly one root selfos-skills aggregate entry")
    if PLUGINS.is_dir():
        for child in sorted(PLUGINS.iterdir()):
            if child.is_dir() and child.resolve() not in registered:
                errors.append(f"{relative(child)}: legacy package is not registered in the marketplace")
        validate_links(errors)
    else:
        errors.append("plugins/: missing")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: validated aggregate Claude adapter and {legacy_count} legacy packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
