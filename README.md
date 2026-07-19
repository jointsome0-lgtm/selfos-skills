# selfos-skills

Portable workflow skills for coding agents. The canonical distribution is the open Agent Skills layout under `skills/`; Claude Code and Codex plugin manifests are thin adapters over the same files, not the repository's organizing principle.

## Install

The recommended path works across Codex, Claude Code, Cursor, OpenCode, Cline, and other Agent Skills-compatible clients:

```bash
npx skills add jointsome0-lgtm/selfos-skills
```

The installer detects available agents and lets you choose skills and scope. Useful non-interactive forms:

```bash
# All skills for Codex, globally
npx skills add jointsome0-lgtm/selfos-skills --skill '*' --agent codex --global --yes

# One skill for Claude Code in the current project
npx skills add jointsome0-lgtm/selfos-skills --skill codebase-design --agent claude-code --yes

# Show the catalog without installing
npx skills add jointsome0-lgtm/selfos-skills --list
```

No clone, working-directory trick, `AGENTS.md` pointer, or prompt-time file path is required.

### Codex native plugin

The repository also ships a root `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`. Register the Git repository as a marketplace, then open `/plugins` and install **selfos-skills**:

```bash
codex plugin marketplace add https://github.com/jointsome0-lgtm/selfos-skills.git
```

The plugin manifest points directly to `./skills/`; it does not mirror or rewrite the catalog.

### Claude Code native plugin

The preferred Claude package is the aggregate plugin over the canonical catalog:

```text
/plugin marketplace add jointsome0-lgtm/selfos-skills
/plugin install selfos-skills@selfos
/reload-plugins
```

The older domain packages (`sdd@selfos`, `design@selfos`, and so on) remain available temporarily for existing installations, but new work belongs under `skills/`.

## Catalog

| Skill | Purpose | Activation |
| --- | --- | --- |
| `codebase-design` | Deep-module vocabulary, seams, adapters, deletion test, testability | automatic or explicit |
| `compose` | Lean outcome-first prompts for GPT/Codex delegation | automatic or explicit |
| `deepen` | Scoped architecture-friction scan and owner decision loop | explicit only |
| `grill-sdd` | Stress-test named SDD sections and land confirmed outcomes | explicit only |
| `grilling` | Shared one-question-at-a-time owner decision primitive | automatic or explicit |
| `sdd-conventions` | Portable SDD conventions plus sync and Decision Log lint scripts | automatic or explicit |
| `slice` | Turn one implementation-ready SDD scope into vertical issues | explicit only |
| `teach` | Stateful multi-session teaching workspace | explicit only |
| `watch` | Codex cloud PR push-review-fix loop | automatic or explicit |

`watch` requires Bash, Git, `gh`, `jq`, network access, and a configured open PR. `sdd-conventions` requires Python 3.9+ for its helper scripts. Other skills are Markdown-first and use only capabilities explicitly available in the host environment.

## Repository layout

```text
skills/<name>/SKILL.md              canonical installable Agent Skill
skills/<name>/references/           bundled docs and self-contained vendored primitives
skills/<name>/scripts/              portable executable helpers
.codex-plugin/plugin.json           thin Codex adapter over ./skills/
.agents/plugins/marketplace.json    Codex marketplace entry
.claude-plugin/plugin.json          thin Claude aggregate adapter
.claude-plugin/marketplace.json     aggregate entry plus legacy packages
AGENTS.md                            generated catalog/fallback, not an installer
plugins/                             legacy Claude domain-package snapshots
scripts/                             catalog validation, indexing, and vendored sync
```

Every top-level skill is independently installable. Where one workflow composes another, `metadata.selfos.vendored-skills` declares canonical sources whose complete folders are copied under `references/<name>/`. CI checks those copies byte for byte, so a selected skill does not depend on sibling installation or host-specific plugin dependency semantics.

## Add or change a skill

A canonical skill follows the Agent Skills specification:

```text
skills/my-skill/
  SKILL.md
  references/    # optional
  scripts/       # optional
  assets/        # optional
```

`SKILL.md` uses only standard top-level fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). Host-specific extensions belong in namespaced `metadata`, never as Claude- or Codex-only top-level keys.

After editing canonical sources:

```bash
python scripts/sync_vendored_skills.py
python scripts/build_index.py
python scripts/validate_skills.py
python scripts/sync_vendored_skills.py --check
python scripts/build_index.py --check
```

The main CI additionally runs the canonical and legacy SDD helper tests, both watcher suites, ShellCheck, the legacy static marketplace validator, a `npx skills` discovery smoke test, and the retained end-to-end Claude marketplace install check.

## Legacy package policy

`plugins/` is a compatibility layer for users already installed through the former Claude Code marketplace structure. It is not the source of truth and should receive only compatibility or security fixes. New skills, shared references, documentation, indexing, and release work are driven from `skills/` and the aggregate adapters.

A later release can remove the legacy packages after downstream installations have migrated to `selfos-skills@selfos` or the universal `skills` installer.

## Public repository rules

Use invented examples only. Do not commit personal data, credentials, private repository excerpts, machine-local paths, or agent/tool state. Skills remain repository-agnostic and must not widen the permissions supplied by the user or host runtime.

## License

MIT. Vendored or adapted material carries its required provenance notice inside the installable skill folder.
