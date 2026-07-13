# selfos-skills

[![Validate](https://github.com/jointsome0-lgtm/selfos-skills/actions/workflows/skill-index.yml/badge.svg)](https://github.com/jointsome0-lgtm/selfos-skills/actions/workflows/skill-index.yml)

Harness-agnostic skills shared across the selfos-ecosystem repositories (`selfos`, `tick-like`, `atlas`, `exp2res`) and standalone personal workflows, also packaged as a Claude Code plugin marketplace. This is the canonical home for skills not tied to a single repository; skills tied to one repository stay in that repository.

## Layout

```
.github/workflows/skill-index.yml ← CI: index check + plugin package validation
.claude-plugin/marketplace.json   ← lists the plugins in this repo
AGENTS.md                         ← agent-neutral discovery index
scripts/build_index.py            ← generates and checks AGENTS.md
scripts/validate_plugins.py       ← validates marketplace.json + plugin manifests
plugins/
  sdd/                            ← SDD-stage workflow skills
    .claude-plugin/plugin.json
    skills/
      grill-sdd/SKILL.md          ← grill an SDD by section; outcomes → SDD edits + issues
  codex-pr/                       ← Codex cloud PR-review loop
    .claude-plugin/plugin.json
    skills/
      watch/SKILL.md              ← push → wait for verdict → fix → repeat until 👍
    scripts/
      codex-pr-watch.sh           ← the poller: exit 0 approved / 2 findings / 3 timeout
  codex-prompting/                ← composing prompts for GPT/Codex delegation
    .claude-plugin/plugin.json
    skills/
      compose/SKILL.md            ← GPT-5.6-era outcome-first prompt guide
  decision/                       ← shared decision primitives
    .claude-plugin/plugin.json
    PROVENANCE.md                 ← upstream pins + license notice for vendored content
    skills/
      grilling/SKILL.md           ← owner decision-interview loop (wrapped by domain skills)
  learning/                       ← multi-session teaching workspaces
    .claude-plugin/plugin.json
    PROVENANCE.md                 ← upstream pin + license notice for vendored content
    skills/
      teach/SKILL.md              ← mission-driven lessons, learning records, glossary
```

One plugin per workflow domain; add a new plugin rather than growing a grab-bag. Every skill body is plain Markdown, with any executable helpers kept as portable scripts.

## Install and discover

### Claude Code

Install once at user scope; the plugin is then available in all projects:

```
/plugin marketplace add jointsome0-lgtm/selfos-skills   # or the local checkout path
/plugin install sdd@selfos
/plugin install codex-pr@selfos
/plugin install codex-prompting@selfos
/plugin install decision@selfos
/plugin install learning@selfos
```

The marketplace inside is named `selfos`, so plugins install as `<plugin>@selfos`.

Skills become available as `/sdd:grill-sdd`, and Claude invokes them by description when relevant — except skills marked `disable-model-invocation: true` (side-effecting workflows like learning's `teach`), which run only when you invoke them explicitly.

### Codex

Clone the repository and start Codex from the clone. Codex reads the root `AGENTS.md`, so matching skills are discoverable without putting their paths in the prompt.

```
git clone https://github.com/jointsome0-lgtm/selfos-skills.git
cd selfos-skills
codex
```

To make the index discoverable outside the clone, optionally add a pointer like this to `~/.codex/AGENTS.md` (using the clone's absolute path):

```markdown
Shared skill index: `/absolute/path/to/selfos-skills/AGENTS.md`. When a task matches, read that file and follow its table.
```

### Any other agent or human

Clone or download the repository, open `AGENTS.md`, choose the matching row, and read the linked `SKILL.md` in full. Follow that file and resolve its relative paths from the skill folder.

## Index maintenance

Regenerate the discovery table after adding or changing skill metadata, then run the same checks used in CI:

```
python scripts/build_index.py
python scripts/build_index.py --check
python scripts/validate_plugins.py
```

## Versioning and update flow

Each plugin has an independent semantic version in its `.claude-plugin/plugin.json`; bump the affected plugin's version whenever that plugin changes. For a notable release, tag the committed change as `<plugin>-v<version>` (for example, `sdd-v0.2.0`) before pushing the commit and tag. Claude Code users can then run `/plugin update sdd@selfos` or enable auto-update.

For live marketplace iteration without reinstalling: `claude --plugin-dir /path/to/selfos-skills/plugins/sdd`.

## Conventions

- Public repository: no personal data, credentials, or local tool state; invented demo content only.
- Skills are repo-agnostic — "this repository's SDD", never hard-coded repo names or paths.
- Skill folder names and frontmatter names are identical kebab-case; descriptions use third-person summary text plus explicit `Use when …` triggers.
- Skills must be self-contained: no references to personal skills or machine-local agent state.

## License

MIT (see [LICENSE](LICENSE)) — the portfolio-wide license for all selfos-ecosystem repositories.
