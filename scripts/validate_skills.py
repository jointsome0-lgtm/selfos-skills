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
    NAME_RE,
    ROOT,
    THIRD_PERSON_RE,
    compare_trees,
    discover_skills,
    display_path,
    symlink_errors,
    validate_provenance,
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


def validate_catalog() -> tuple[int, list[str]]:
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
        if not skill.description or len(skill.description) > 1024:
            errors.append(f"{relative}: description must be 1-1024 characters")
        summary, separator, trigger = skill.description.partition(". Use when ")
        if not separator or not summary or not trigger.strip():
            errors.append(
                f"{relative}: description must be a third-person summary followed by '. Use when …'"
            )
        elif not THIRD_PERSON_RE.match(summary):
            errors.append(f"{relative}: description must begin in third-person form")
        compatibility = skill.fields.get("compatibility")
        if compatibility is not None and not (1 <= len(compatibility) <= 500):
            errors.append(f"{relative}: compatibility must be 1-500 characters")
        if not skill.body:
            errors.append(f"{relative}: Markdown body must not be empty")
        elif len(skill.body.splitlines()) > 500:
            errors.append(f"{relative}: SKILL.md body must stay under 500 lines")

        explicit = skill.metadata.get("selfos.explicit-only")
        if explicit is not None and explicit.casefold() not in {"true", "false"}:
            errors.append(f"{relative}: selfos.explicit-only must be the string 'true' or 'false'")
        disable = skill.fields.get("disable-model-invocation")
        if disable is not None and disable != "true":
            errors.append(f"{relative}: disable-model-invocation must be the literal true")
        elif (disable == "true") != skill.explicit_only:
            errors.append(
                f"{relative}: disable-model-invocation and selfos.explicit-only 'true' must be set together"
            )

        tree_errors = symlink_errors(skill.root)
        errors.extend(tree_errors)
        if tree_errors:
            continue

        vendored = skill.vendored_skills
        validate_provenance(skill.root, errors, vendored)

        if len(set(vendored)) != len(vendored):
            errors.append(f"{relative}: selfos.vendored-skills contains duplicates")
        for dependency in vendored:
            if dependency == skill.name:
                errors.append(f"{relative}: a skill cannot vendor itself")
                continue
            source = by_name.get(dependency)
            if source is None:
                errors.append(f"{relative}: unknown vendored skill {dependency!r}")
                continue
            if source.vendored_skills:
                errors.append(
                    f"{relative}: vendored skill {dependency!r} itself vendors skills; flatten the composition"
                )
            destination = skill.root / "references" / dependency
            errors.extend(compare_trees(source.root, destination))

        errors.extend(validate_links(skill.root))

    return len(skills), errors


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


def validate_adapters() -> list[str]:
    errors: list[str] = []
    codex = load_json(ROOT / ".codex-plugin" / "plugin.json", errors)
    claude = load_json(ROOT / ".claude-plugin" / "plugin.json", errors)
    codex_marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json", errors)
    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json", errors)

    versions: set[str] = set()
    for label, manifest in (("Codex", codex), ("Claude", claude)):
        if manifest is None:
            continue
        if manifest.get("name") != "selfos-skills":
            errors.append(f"{label} manifest name must be 'selfos-skills'")
        version = manifest.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
            errors.append(f"{label} manifest version must be semantic X.Y.Z")
        else:
            versions.add(version)
    if len(versions) > 1:
        errors.append("Codex and Claude aggregate manifests must have the same version")
    if codex is not None and codex.get("skills") != "./skills/":
        errors.append(".codex-plugin/plugin.json must point skills at './skills/'")

    if codex_marketplace is not None:
        entries = codex_marketplace.get("plugins")
        matching = [entry for entry in entries or [] if isinstance(entry, dict) and entry.get("name") == "selfos-skills"]
        if len(matching) != 1:
            errors.append("Codex marketplace must contain exactly one selfos-skills entry")
        else:
            source = matching[0].get("source")
            if source != {"source": "local", "path": "./"}:
                errors.append("Codex marketplace selfos-skills source must be local path './'")

    if claude_marketplace is not None:
        entries = claude_marketplace.get("plugins")
        matching = [entry for entry in entries or [] if isinstance(entry, dict) and entry.get("name") == "selfos-skills"]
        if len(matching) != 1:
            errors.append("Claude marketplace must contain exactly one aggregate selfos-skills entry")
        elif matching[0].get("source") != "./":
            errors.append("Claude marketplace aggregate source must be './'")

    return errors


def main() -> int:
    count, errors = validate_catalog()
    errors.extend(validate_adapters())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: validated {count} portable Agent Skills and both host adapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
