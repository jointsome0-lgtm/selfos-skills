#!/usr/bin/env python3
"""Validate the canonical Agent Skills catalog and thin host adapters."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

from skill_catalog import (
    ALLOWED_FIELDS,
    BUNDLE_ENTRYPOINT_NAME,
    BUNDLE_MANIFEST_NAME,
    CONTROL_RE,
    GENERATED_MARKER_NAME,
    NAME_RE,
    ROOT,
    Skill,
    compatibility_errors,
    derive_adapter_version,
    discover_skills,
    display_path,
    load_bundle_manifest,
    parse_semver,
    symlink_errors,
    validate_provenance,
    version_errors,
)

LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
FENCE_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")


def strip_fenced_blocks(text: str) -> str:
    kept: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if fence_character is None:
            if match:
                fence = match.group(1)
                fence_character = fence[0]
                fence_length = len(fence)
                kept.append("")
                continue
            kept.append(line)
            continue
        if match:
            fence = match.group(1)
            if fence[0] == fence_character and len(fence) >= fence_length:
                fence_character = None
                fence_length = 0
        kept.append("")
    return "\n".join(kept)


def local_link_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if " " in target:
        target = target.split(" ", 1)[0]
    target = unquote(target)
    lowered = target.casefold()
    if not target or target.startswith("#"):
        return None
    if lowered.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return None
    return target.split("#", 1)[0].split("?", 1)[0]


def validate_links(skill_root: Path) -> list[str]:
    errors: list[str] = []
    canonical_root = skill_root.resolve()
    for markdown in sorted(skill_root.rglob("*.md")):
        try:
            text = markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{display_path(markdown)}: cannot read UTF-8 Markdown: {exc}")
            continue
        for match in LINK_RE.finditer(strip_fenced_blocks(text)):
            target = local_link_target(match.group("target"))
            if target is None:
                continue
            if target.startswith("/"):
                errors.append(f"{display_path(markdown)}: local link must be relative: {target}")
                continue
            candidate = (markdown.parent / target).resolve()
            try:
                candidate.relative_to(canonical_root)
            except ValueError:
                errors.append(
                    f"{display_path(markdown)}: link escapes the installable skill folder: {target}"
                )
                continue
            if not candidate.exists():
                errors.append(f"{display_path(markdown)}: missing local link target: {target}")
    return errors


def validate_catalog() -> tuple[list[Skill], list[str]]:
    skills, errors = discover_skills()
    by_name = {skill.name: skill for skill in skills}
    if len(by_name) != len(skills):
        seen: set[str] = set()
        for skill in skills:
            if skill.name in seen:
                errors.append(f"{display_path(skill.path)}: duplicate skill name {skill.name!r}")
            seen.add(skill.name)

    for skill in skills:
        relative = display_path(skill.path)
        unknown = sorted(set(skill.fields) - ALLOWED_FIELDS)
        for key in unknown:
            errors.append(
                f"{relative}: unsupported top-level frontmatter field {key!r}; use metadata for extensions"
            )
        if len(skill.name) > 64 or not NAME_RE.fullmatch(skill.name):
            errors.append(
                f"{relative}: name must be 1-64 lowercase letters/digits with single hyphens"
            )
        if skill.name != skill.root.name:
            errors.append(
                f"{relative}: name {skill.name!r} must match folder {skill.root.name!r}"
            )
        if not skill.description or len(skill.description) > 500:
            errors.append(
                f"{relative}: description must be 1-500 characters; hosts truncate"
                " long catalog entries tail-first"
            )
        if not skill.description.startswith("Use when ") or not skill.description[len("Use when "):].strip():
            errors.append(
                f"{relative}: description must start with 'Use when …' — it is the"
                " invocation trigger; the SKILL.md body carries the rest"
            )
        compatibility = skill.fields.get("compatibility")
        if compatibility is not None and not (1 <= len(compatibility) <= 500):
            errors.append(f"{relative}: compatibility must be 1-500 characters")
        errors.extend(compatibility_errors(skill))
        errors.extend(version_errors(skill))
        if not skill.body:
            errors.append(f"{relative}: Markdown body must not be empty")
        elif len(skill.body.splitlines()) > 500:
            errors.append(f"{relative}: SKILL.md body must stay under 500 lines")

        explicit = skill.metadata.get("selfos.explicit-only")
        if explicit is not None and explicit.casefold() not in {"true", "false"}:
            errors.append(f"{relative}: selfos.explicit-only must be the string 'true' or 'false'")
        disable = skill.fields.get("disable-model-invocation")
        if disable is not None:
            if disable.strip().casefold() != "true":
                errors.append(
                    f"{relative}: disable-model-invocation must be 'true' when present"
                )
            if not skill.explicit_only:
                errors.append(
                    f"{relative}: disable-model-invocation requires"
                    " metadata selfos.explicit-only 'true'"
                )
        elif skill.explicit_only:
            errors.append(
                f"{relative}: explicit-only skills must set top-level"
                " disable-model-invocation 'true' so Claude hosts enforce the guard"
            )

        tree_errors = symlink_errors(skill.root)
        errors.extend(tree_errors)
        if tree_errors:
            continue

        if "selfos.vendored-skills" in skill.metadata:
            errors.append(
                f"{relative}: metadata selfos.vendored-skills was replaced by the "
                f"{BUNDLE_MANIFEST_NAME} dependency manifest; declare bundled "
                "dependencies there and keep canonical frontmatter host-agnostic"
            )
        if (skill.root / GENERATED_MARKER_NAME).is_file():
            errors.append(
                f"{relative}: canonical skills must not ship a top-level "
                f"{GENERATED_MARKER_NAME}; the name is reserved for generated bundle copies"
            )
        # Hosts discover skills by recursively scanning for SKILL.md, so any
        # nested file with that name leaks into their catalogs as a separate
        # skill; bundled dependency entrypoints are renamed instead.
        for nested in sorted(skill.root.rglob("SKILL.md")):
            if nested == skill.path:
                continue
            errors.append(
                f"{display_path(nested)}: only skills/<name>/SKILL.md may use the "
                "name SKILL.md — nested copies leak into hosts' recursive skill "
                f"discovery; bundle entrypoints are renamed to {BUNDLE_ENTRYPOINT_NAME}"
            )
        # Graph and byte-level bundle checks live in scripts/build_bundles.py
        # (--check in CI); here the manifest only feeds provenance delegation.
        dependencies, bundle_errors = load_bundle_manifest(skill.root)
        errors.extend(bundle_errors)
        validate_provenance(skill.root, errors, dependencies or ())

        errors.extend(validate_links(skill.root))

    return skills, errors


def load_json(path: Path, errors: list[str]) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{display_path(path)}: required adapter file is missing")
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{display_path(path)}: invalid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{display_path(path)}: top-level JSON value must be an object")
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


def validate_claude_adapter(manifest: dict | None, marketplace: dict | None) -> list[str]:
    """Validate the aggregate-only Claude adapter and marketplace metadata."""
    errors: list[str] = []
    manifest_where = ".claude-plugin/plugin.json"
    if manifest is not None:
        required_text(manifest, "description", manifest_where, errors)

    if marketplace is None:
        return errors

    where = ".claude-plugin/marketplace.json"
    marketplace_name = required_text(marketplace, "name", where, errors)
    if marketplace_name is not None and not NAME_RE.fullmatch(marketplace_name):
        errors.append(f"{where}: marketplace name {marketplace_name!r} must be kebab-case")

    owner = marketplace.get("owner")
    if not isinstance(owner, dict):
        errors.append(f"{where}: owner must be an object")
    else:
        required_text(owner, "name", f"{where}: owner", errors)

    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        errors.append("Claude marketplace must contain exactly one selfos-skills entry")
        return errors

    entry = entries[0]
    item_where = f"{where}: plugins[0]"
    if not isinstance(entry, dict):
        errors.append(f"{item_where}: must be an object")
        return errors
    name = required_text(entry, "name", item_where, errors)
    source = required_text(entry, "source", item_where, errors)
    required_text(entry, "description", item_where, errors)
    if name is not None and name != "selfos-skills":
        errors.append(f"{item_where}: name must be 'selfos-skills'")
    if source is not None and source != "./":
        errors.append(f"{item_where}: source must be './'")
    return errors


def validate_adapters(skills: list[Skill]) -> list[str]:
    errors: list[str] = []
    codex = load_json(ROOT / ".codex-plugin" / "plugin.json", errors)
    claude = load_json(ROOT / ".claude-plugin" / "plugin.json", errors)
    codex_marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json", errors)
    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json", errors)

    expected_version, _ = derive_adapter_version(skills, ROOT)
    for label, manifest in (("Codex", codex), ("Claude", claude)):
        if manifest is None:
            continue
        if manifest.get("name") != "selfos-skills":
            errors.append(f"{label} manifest name must be 'selfos-skills'")
        version = manifest.get("version")
        if not isinstance(version, str) or parse_semver(version) is None:
            errors.append(f"{label} manifest version must be semantic X.Y.Z")
        elif expected_version is not None and version != expected_version:
            errors.append(
                f"{label} manifest version {version!r} is stale; "
                f"the canonical catalog derives {expected_version!r}"
            )
    if codex is not None and codex.get("skills") != "./skills/":
        errors.append(".codex-plugin/plugin.json must point skills at './skills/'")

    errors.extend(validate_claude_adapter(claude, claude_marketplace))

    if codex_marketplace is not None:
        entries = codex_marketplace.get("plugins")
        matching = [entry for entry in entries or [] if isinstance(entry, dict) and entry.get("name") == "selfos-skills"]
        if len(matching) != 1:
            errors.append("Codex marketplace must contain exactly one selfos-skills entry")
        else:
            source = matching[0].get("source")
            if source != {"source": "local", "path": "./"}:
                errors.append("Codex marketplace selfos-skills source must be local path './'")

    return errors


def main() -> int:
    skills, errors = validate_catalog()
    errors.extend(validate_adapters(skills))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: validated {len(skills)} portable Agent Skills and both host adapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
