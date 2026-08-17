---
name: compose
description: Use when work is about to be delegated to another model or agent — Codex, a Claude subagent, or similar — and needs a prompt or agent instructions; produces a lean, outcome-first delegate prompt with a dated model and effort choice.
compatibility: Host-neutral Markdown guidance; no required tools, OS constraints, write access, or external integrations. Network access is optional for refreshing linked provider guidance.
metadata:
  selfos.version: "0.2.2"
---

# Composing delegated prompts

How to write prompts that delegate work to another model or agent. This file holds only what follows from delegation itself — the delegate lacks the delegator's context, so certain information must always be conveyed. Everything empirical about how a specific model behaves lives in a dated per-model reference:

| Target | Reference |
| --- | --- |
| GPT-5.6 family (`gpt-5.6-sol` / `-terra` / `-luna`), Codex CLI/cloud runs | [references/gpt-5.6.md](references/gpt-5.6.md) |
| Claude Fable 5 (`fable-5`; API `claude-fable-5`) | [references/claude-fable-5.md](references/claude-fable-5.md) |
| Claude Opus 5 (`opus-5`; API `claude-opus-5`) | [references/claude-opus-5.md](references/claude-opus-5.md) |

Read the matching reference before composing; choosing the model is part of composing, so when the model is not fixed yet, skim the model-choice section of each candidate reference first. **On any conflict, the per-model reference wins over this file.** The core is a default, not a dogma: models change between versions, and a model that breaks these defaults is handled by editing its reference, not by relitigating the core.

Maintenance: a new model gets a new reference file plus a routing row here — the core stays untouched. Every reference must open with its upstream source URL(s) and a "Checked against upstream YYYY-MM-DD" line, so staleness is visible and refreshing needs no archaeology.

## The delegation contract

A delegated run cannot read your mind, your conversation, or your risk tolerance. Whatever the target model, the prompt must convey:

- **Goal** — the outcome and why it matters, in one or two sentences.
- **Context** — domain facts the delegate cannot infer: layout hints, prior decisions, links to authoritative documents.
- **Constraints** — hard limits only: protected paths, do-not-commit, compatibility, no new dependencies.
- **Success criteria** — observable checks: what must be true when the work is done, and what evidence the answer must include.
- **Tools** — which tools to use, when, and what not to use (when the delegate's toolset is not self-evident).
- **Output** — the deliverable and its format: diff, PR, report structure. For a subagent run, the final message is the deliverable.
- **Stop rules** — when to retry, fall back, abstain, ask, or stop. Bound loops ("stop when <condition>; retry transient failures at most N times; do not repeat completed side-effecting calls"). Missing evidence means a structured failure, not a guess: "if you cannot establish X, stop and report what is missing."
- **Autonomy boundary** — what the run may do without pausing and where it must stop, plus which ambiguities warrant a question back and which the delegate may resolve itself. A compact policy, stated once, is enough — adapt this one:

```text
For requests to answer, explain, review, diagnose, or plan: inspect the relevant
materials and report the result; do not implement changes unless asked.
For requests to change, build, or fix: make in-scope local changes and run
non-destructive validation without asking first.
Require confirmation for external writes, destructive actions, purchases, or a
material expansion of scope.
```

Use these as markdown sections in roughly this order and omit what the task does not need. How lean or prescriptive the surrounding prose should be, which verification instructions to add or omit, and how to phrase steering are per-model questions — see the references.

## Effort policy (operating canon)

The working ladder for delegated runs is `low`–`high`, whatever the provider's parameter range: `medium` for routine bounded work, `high` for the hardest delegated work, `low` for latency-sensitive or relay work when quality holds. Never select `xhigh` or `max` for a build, review, or verification run — those tiers are reserved for a live design pass the owner explicitly requests. This policy is canonical over any upstream effort ladder; when a reference relays an upstream recommendation above `high`, the ceiling here still applies. Before raising effort, check the prompt first: a missing success criterion or stop rule is cheaper to fix than a higher tier.

## Example

```markdown
## Goal
Make webhook replays idempotent in the payment handler; duplicates currently
double-write the ledger.

## Context
Handlers live in `src/webhooks/`; the idempotency-key scheme is documented in
`docs/idempotency.md`.

## Constraints
NEVER edit `src/billing/ledger.*`. No new dependencies.

## Success criteria
- Replaying a webhook with the same key produces exactly one ledger write.
- `npm test -- webhooks` passes; include the output.

## Stop rules
If the root cause is outside `src/webhooks/`, stop and report instead of
expanding scope.

## Output
A focused diff plus a three-line summary: cause, fix, evidence.
```
