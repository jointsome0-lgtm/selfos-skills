# selfos-skills

Claude Code plugin marketplace with skills shared across the selfos-ecosystem repositories (`selfos`, `tick-like`, `atlas`, `exp2res`). Canonical home for cross-repo workflow skills; skills tied to one repository's specifics stay in that repo's `.claude/skills/`.

## Layout

```
.claude-plugin/marketplace.json   ← lists the plugins in this repo
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
```

One plugin per workflow domain; add a new plugin rather than growing a grab-bag.

## Install (once, user scope — applies in all projects)

```
/plugin marketplace add jointsome0-lgtm/selfos-skills   # or the local checkout path
/plugin install sdd@selfos
```

The marketplace inside is named `selfos`, so plugins install as `<plugin>@selfos`.

Skills become available as `/sdd:grill-sdd`, and Claude invokes them by description when relevant.

## Update flow

`plugin.json` deliberately has no `version` field, so every commit is a new version:
edit → commit → push → `/plugin update sdd@selfos` (or enable auto-update).
For live iteration without reinstalling: `claude --plugin-dir ~/projects/selfos-skills/plugins/sdd`.

## Conventions

- Public repository: no personal data, credentials, or local tool state; invented demo content only.
- Skills are repo-agnostic — "this repository's SDD", never hard-coded repo names or paths.
- Skills must be self-contained: no references to personal skills in `~/.claude/skills`.
