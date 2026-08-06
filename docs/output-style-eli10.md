# ELI10 output style

The owner's global Claude Code output style: plain short language,
outcome-first reporting, and decisions presented as a few explained options
with a reasoned recommendation. It lowers day-to-day cognitive load without
touching what the agent actually does.

This is a Claude Code host-specific artifact, not an Agent Skill, so it lives
here rather than under `skills/` — no catalog entry, no version machinery.
Companion to the `wait-what` skill
([issue #110](https://github.com/jointsome0-lgtm/selfos-skills/issues/110)):
the style is the permanent register, `wait-what` is the one-shot "re-pitch
that" recovery when a message still did not land.

## Artifact

The style file itself lives verbatim at
[`docs/output-styles/eli10.md`](output-styles/eli10.md) (iterated
2026-08-06), ready to copy as-is — this page is only the install note and
the decision record around it.

## Install

```bash
mkdir -p ~/.claude/output-styles
cp docs/output-styles/eli10.md ~/.claude/output-styles/
```

Then select it in user settings (`~/.claude/settings.json`):

```json
{
  "outputStyle": "ELI10"
}
```

## Wording decisions (settled with the owner, 2026-08-06 — do not relitigate)

- "curious 10-year-old" in the opening line (general disposition: explain the
  *why* everywhere) **and** the direct "I want to understand the choice, not
  just pick fast" in the decision paragraph (understanding as an explicit
  goal) are both intentional — curiosity alone was judged insufficient, and
  the direct want survives paraphrase pressure better than a `so I
  understand` purpose clause.
- "understand" over "learn": understanding is for applying, not studying for
  its own sake.
- The decision paragraph was deliberately compressed back to two sentences
  after a longer draft; don't expand it.

Origin: started as a copy of the ELI5 style from a widely shared community
screenshot and was substantially rewritten.
