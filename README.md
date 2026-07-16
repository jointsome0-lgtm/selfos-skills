# selfos-skills

[![Validate](https://github.com/jointsome0-lgtm/selfos-skills/actions/workflows/skill-index.yml/badge.svg)](https://github.com/jointsome0-lgtm/selfos-skills/actions/workflows/skill-index.yml)

Harness-agnostic skills shared across the selfos-ecosystem repositories (`selfos`, `ephemeris`, `atlas`, `exp2res`) and standalone personal workflows, also packaged as a Claude Code plugin marketplace. This is the canonical home for skills not tied to a single repository; skills tied to one repository stay in that repository.

## Layout

```
.github/workflows/skill-index.yml ← CI: index, plugin, and conventions checks
.claude-plugin/marketplace.json   ← lists the plugins in this repo
AGENTS.md                         ← agent-neutral discovery index
scripts/build_index.py            ← generates and checks AGENTS.md
scripts/validate_plugins.py       ← validates marketplace.json + plugin manifests
plugins/
  sdd/                            ← SDD-stage workflow skills + shared conventions
    .claude-plugin/plugin.json
    conventions/
      SDD-CONVENTIONS.md          ← versioned cross-repo template SDD repos vendor
      DECISION-LOG.md             ← decision-log entry grammar + lint semantics
      README.md                   ← distribution model: embed, sync, offline check
    scripts/
      sync_conventions.py         ← stdlib sync/check tool (single file, vendorable)
      check_decision_log.py       ← decision-log lint (graduated size thresholds)
    PROVENANCE.md                 ← upstream pin + license notice for vendored content
    skills/
      grill-sdd/SKILL.md          ← grill an SDD by section; outcomes → SDD edits + issues
      slice/SKILL.md              ← slice an approved SDD scope into vertical tickets
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
  design/                         ← architecture design vocabulary and methods
    .claude-plugin/plugin.json
    PROVENANCE.md                 ← upstream pins + license notice for vendored content
    skills/
      codebase-design/SKILL.md    ← deep modules, seams, adapters, deletion test
        DEEPENING.md              ← dependency categories, seam discipline
        DESIGN-IT-TWICE.md        ← 3+ independent interface designs, then compare
      deepen/SKILL.md             ← scoped scan → ephemeral offline report → owner decision loop
        HTML-REPORT.md            ← script-free offline report scaffold + diagram patterns
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
/plugin install design@selfos
/plugin install learning@selfos
```

The marketplace inside is named `selfos`, so plugins install as `<plugin>@selfos`. `sdd`'s `grill-sdd` and `design`'s `deepen` wrap `decision`'s `grilling` interview loop; both plugins declare that dependency in their manifests, so installing `sdd@selfos` or `design@selfos` pulls `decision@selfos` in automatically (Claude Code ≥ 2.1.110 — on older versions, install both explicitly).

Skills become available as `/sdd:grill-sdd`, and Claude invokes them by description when relevant — except skills marked `disable-model-invocation: true` (owner-facing or side-effecting workflows like learning's `teach` and sdd's `grill-sdd`), which run only when you invoke them explicitly.

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
python plugins/sdd/scripts/test_sync_conventions.py
python plugins/sdd/scripts/test_check_decision_log.py
shellcheck scripts/*.sh plugins/*/scripts/*.sh
bats plugins/codex-pr/scripts/test_codex_pr_watch.bats
./scripts/check_plugin_install.sh
```

## Versioning and update flow

Each plugin has an independent semantic version in its `.claude-plugin/plugin.json`; bump the affected plugin's version whenever that plugin changes. Every version bump gets a tag on the commit that lands it, created with the CLI so plugin.json and the marketplace entry are validated to agree:

```
claude plugin tag plugins/sdd --push
```

Tags follow the CLI's `{name}--v{version}` format (for example, `sdd--v0.6.2`). Claude Code users can then run `/plugin update sdd@selfos` or enable auto-update.

Periodically — after a batch of related bumps lands — a `bundle-YYYY-MM-DD` tag plus a GitHub Release records which plugin versions were validated together; the latest Release is the stable distribution point.

For live marketplace iteration without reinstalling: `claude --plugin-dir /path/to/selfos-skills/plugins/sdd`.

## Conventions

- Public repository: no personal data, credentials, or local tool state; invented demo content only.
- Skills are repo-agnostic — "this repository's SDD", never hard-coded repo names or paths.
- Skill folder names and frontmatter names are identical kebab-case; descriptions use third-person summary text plus explicit `Use when …` triggers.
- Skills must be self-contained: no references to personal skills or machine-local agent state.

## License

MIT (see [LICENSE](LICENSE)) — the portfolio-wide license for all selfos-ecosystem repositories.
