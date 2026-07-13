#!/usr/bin/env python3
"""Validate the plugin package: marketplace.json schema, source paths, and plugin manifests."""

from __future__ import annotations

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

    if PLUGINS_DIR.is_dir():
        registered_dirs = {path for path in registered.values()}
        for child in sorted(PLUGINS_DIR.iterdir()):
            if child.is_dir() and child.resolve() not in registered_dirs:
                errors.append(
                    f"plugins/{child.name}: directory is not registered in {display_path(MARKETPLACE_PATH)}"
                )
    else:
        errors.append("plugins/: directory is missing")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: validated marketplace.json and {plugin_count} plugin manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
