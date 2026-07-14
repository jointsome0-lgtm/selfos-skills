#!/usr/bin/env python3
"""Validate the plugin package: marketplace.json schema, source paths, and plugin manifests."""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = ROOT / "plugins"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
NO_VENDOR_MARKER = "No vendored content."
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE_LINE_RE = re.compile(r"^ {0,3}(?:`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def display_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json_object(path: Path, errors: list[str]) -> dict | None:
    relative = display_path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"{relative}: file is missing")
        return None
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: cannot read UTF-8 file: {exc}")
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"{relative}:{exc.lineno}: invalid JSON: {exc.msg}")
        return None

    if not isinstance(data, dict):
        errors.append(f"{relative}: top level must be a JSON object")
        return None
    return data


def text_field(data: dict, key: str, where: str, errors: list[str]) -> str | None:
    value = data.get(key)
    if value is None:
        errors.append(f"{where}: missing required field {key!r}")
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: field {key!r} must be non-empty text")
        return None
    if CONTROL_RE.search(value):
        errors.append(f"{where}: field {key!r} must not contain control characters")
        return None
    return value


def validate_marketplace_entry(entry: object, index: int, errors: list[str]) -> tuple[str, Path] | None:
    where = f"{display_path(MARKETPLACE_PATH)}: plugins[{index}]"
    if not isinstance(entry, dict):
        errors.append(f"{where}: must be a JSON object")
        return None

    name = text_field(entry, "name", where, errors)
    source = text_field(entry, "source", where, errors)
    text_field(entry, "description", where, errors)
    if name is None or source is None:
        return None

    if not NAME_RE.fullmatch(name):
        errors.append(f"{where}: name {name!r} must be kebab-case (lowercase letters, digits, single hyphens)")

    if not source.startswith("./plugins/"):
        errors.append(f"{where}: source {source!r} must point into ./plugins/")
        return None
    source_path = (ROOT / source).resolve()
    if not source_path.is_dir():
        errors.append(f"{where}: source {source!r} does not resolve to a directory")
        return None
    if source_path.parent != PLUGINS_DIR.resolve():
        errors.append(f"{where}: source {source!r} must be a direct child of ./plugins/")
        return None
    if source_path.name != name:
        errors.append(f"{where}: name {name!r} must match its source directory {source_path.name!r}")
        return None
    return name, source_path


def check_pin(chunk: str, where: str, errors: list[str]) -> None:
    labeled = re.findall(r"(?i)\b(?:blob|commit|merge)\b[^\r\n]*?\b([0-9a-f]{40})\b", chunk)
    if not labeled:
        errors.append(
            f"{where}: must pin upstream content to a labeled 40-hex SHA (blob/commit/merge …)"
        )
    if "0" * 40 in re.findall(r"(?i)\b[0-9a-f]{40}\b", chunk):
        errors.append(f"{where}: pins must be real SHAs, not the all-zero placeholder")


def check_import_date(chunk: str, where: str, errors: list[str]) -> None:
    imported = re.search(r"\bImported\b", chunk)
    date_valid = False
    if imported is not None:
        for match in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", chunk[imported.end():]):
            try:
                datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                continue
            date_valid = True
            break
    if not date_valid:
        errors.append(f"{where}: must record a real import date (Imported … YYYY-MM-DD)")


def validate_provenance(plugin_dir: Path, errors: list[str]) -> None:
    """Every plugin declares provenance in PROVENANCE.md.

    A plugin with nothing vendored opens its only statement besides headings
    with "No vendored content." — anywhere else the marker is an error, so it
    can never silence the checks for vendored sections appended after it.
    Every "##" section is a vendored item carrying its own labeled 40-hex
    pin — with no all-zero placeholder anywhere in the section — and real
    import date, so one pinned section cannot vouch for another and no
    heading shape escapes the checks; the sole exemption is the license
    notice, a slash-free heading naming "license"; the upstream license notice is checked
    file-wide because one upstream's notice may cover several sections. These
    are presence-and-shape checks against forgetting, not cryptographic
    verification: whether a pin matches the upstream bytes, or a notice its
    upstream, is established in PR review.
    """
    provenance_path = plugin_dir / "PROVENANCE.md"
    relative = display_path(provenance_path)

    if provenance_path.is_symlink():
        errors.append(f"{relative}: must be a regular file, not a symlink")
        return
    if not provenance_path.exists():
        errors.append(
            f"{relative}: missing; pin vendored sources or state \"No vendored content.\""
        )
        return
    if not provenance_path.is_file():
        errors.append(f"{relative}: must be a regular file")
        return
    try:
        if provenance_path.stat().st_size > 64 * 1024:
            errors.append(f"{relative}: implausibly large (over 64 KiB)")
            return
        text = provenance_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: cannot read UTF-8 file: {exc}")
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
            f"{relative}: {NO_VENDOR_MARKER!r} must open the file's only statement "
            f"besides headings; with vendored sections present, drop the marker and pin them"
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
            where = f"{relative}: section {heading!r}"
            check_pin(body, where, errors)
            check_import_date(body, where, errors)
    else:
        check_pin(text, relative, errors)
        check_import_date(text, relative, errors)

    notice_complete = (
        re.search(r"Copyright \(c\) \d{4}", text, re.IGNORECASE)
        and "Permission is hereby granted" in text
        and "The above copyright notice and this permission notice" in text
        and 'THE SOFTWARE IS PROVIDED "AS IS"' in text
    )
    if not notice_complete:
        errors.append(
            f"{relative}: must carry the full upstream license notice "
            f"(copyright line, permission grant, notice condition, warranty disclaimer)"
        )


def validate_plugin_manifest(name: str, plugin_dir: Path, errors: list[str]) -> None:
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    manifest = load_json_object(manifest_path, errors)
    if manifest is None:
        return

    relative = display_path(manifest_path)
    manifest_name = text_field(manifest, "name", relative, errors)
    version = text_field(manifest, "version", relative, errors)
    text_field(manifest, "description", relative, errors)

    if manifest_name is not None and manifest_name != name:
        errors.append(f"{relative}: name {manifest_name!r} must match marketplace entry {name!r}")
    if version is not None and not VERSION_RE.fullmatch(version):
        errors.append(f"{relative}: version {version!r} must be MAJOR.MINOR.PATCH")


def validate_relative_links(errors: list[str]) -> None:
    """Every relative Markdown link in plugin content resolves inside the repository.

    Fenced code blocks and inline code spans are ignored; http(s)/mailto and
    pure-anchor targets are out of scope. This is a resolution check, not a
    content check: it exists so a skill's companion references (for example
    DEEPENING.md next to a SKILL.md) cannot silently go missing or dangle.
    """
    root = ROOT.resolve()
    for md_path in sorted(PLUGINS_DIR.glob("**/*.md")):
        relative_md = display_path(md_path)
        try:
            lines = md_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative_md}: cannot read UTF-8 file: {exc}")
            continue
        in_fence = False
        for line_number, line in enumerate(lines, start=1):
            if FENCE_LINE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for target in MD_LINK_RE.findall(INLINE_CODE_RE.sub("", line)):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                bare_target = target.split("#", 1)[0]
                if not bare_target:
                    continue
                resolved = (md_path.parent / bare_target).resolve()
                if not resolved.exists():
                    errors.append(
                        f"{relative_md}:{line_number}: relative link target {target!r} does not exist"
                    )
                elif root != resolved and root not in resolved.parents:
                    errors.append(
                        f"{relative_md}:{line_number}: relative link target {target!r} escapes the repository"
                    )


def main() -> int:
    errors: list[str] = []
    registered: dict[str, Path] = {}
    plugin_count = 0

    marketplace = load_json_object(MARKETPLACE_PATH, errors)
    if marketplace is not None:
        where = display_path(MARKETPLACE_PATH)
        marketplace_name = text_field(marketplace, "name", where, errors)
        if marketplace_name is not None and not NAME_RE.fullmatch(marketplace_name):
            errors.append(f"{where}: marketplace name {marketplace_name!r} must be kebab-case")

        owner = marketplace.get("owner")
        if not isinstance(owner, dict):
            errors.append(f"{where}: missing required object field 'owner'")
        else:
            text_field(owner, "name", f"{where}: owner", errors)

        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            errors.append(f"{where}: 'plugins' must be a non-empty list")
        else:
            plugin_count = len(plugins)
            for index, entry in enumerate(plugins):
                resolved = validate_marketplace_entry(entry, index, errors)
                if resolved is None:
                    continue
                name, source_path = resolved
                if name in registered:
                    errors.append(f"{where}: plugins[{index}]: duplicate plugin name {name!r}")
                    continue
                registered[name] = source_path
                validate_plugin_manifest(name, source_path, errors)
                validate_provenance(source_path, errors)

    if PLUGINS_DIR.is_dir():
        registered_dirs = {path for path in registered.values()}
        for child in sorted(PLUGINS_DIR.iterdir()):
            if child.is_dir() and child.resolve() not in registered_dirs:
                errors.append(
                    f"plugins/{child.name}: directory is not registered in {display_path(MARKETPLACE_PATH)}"
                )
    else:
        errors.append("plugins/: directory is missing")

    if PLUGINS_DIR.is_dir():
        validate_relative_links(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: validated marketplace.json and {plugin_count} plugin manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
