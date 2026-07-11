---
name: compose
description: Composes lean, outcome-first prompts for the GPT-5.6 model family (gpt-5.6-sol / -terra / -luna) and Codex runs — goal, success criteria, constraints, autonomy boundary, stop rules, and model/effort choice. Use when delegating coding, review, diagnosis, or research work to Codex or another GPT-backed agent, or when writing or updating a prompt or agent instructions for one.
---

# Composing GPT-5.6 / Codex prompts

How to write prompts that delegate work to the GPT-5.6 model family — `gpt-5.6-sol` (flagship; the `gpt-5.6` alias routes here), `gpt-5.6-terra` (balanced cost), `gpt-5.6-luna` (high-volume) — in the Codex CLI, Codex cloud, or the API. Current as of the July 2026 GPT-5.6 release; sources: OpenAI's [GPT-5.6 prompting guide](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6) and [GPT-5.6 model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6).

## Core principle: lean and outcome-first

Describe the outcome, not the procedure. In OpenAI's internal coding-agent evals, leaner prompts scored roughly 10–15% higher while cutting total tokens 41–66%. GPT-5.6 infers the intended level of work from context, so provide domain context, hard constraints, boundaries, and success criteria — do not prescribe every step.

- One task per run.
- State each instruction once; delete repeated rules and redundant examples.
- Turn process steps into success criteria: "tests X and Y pass", not "first run X, then run Y".
- Keep an example only when it encodes a real requirement or corrects a measured gap.

## Prompt skeleton

Markdown sections, roughly in this order; omit what the task does not need.

```markdown
## Goal
One or two sentences: the outcome and why it matters.

## Context
Domain facts the model cannot infer: layout hints, prior decisions, links.

## Constraints
Hard limits only — protected paths, do-not-commit, compatibility, no new dependencies.

## Success criteria
Observable checks: what must be true, and what evidence the answer must include.

## Output
The deliverable and its format (diff, PR, report structure). For a subagent run,
the final message is the deliverable.
```

Reserve ALWAYS/NEVER for true invariants (a binding AGENTS.md, do-not-touch files). Everything else reads better as a success criterion.

## Autonomy boundary

GPT-5.6 is proactive and persistent on multi-step tasks; say what the run may do without pausing and where it must stop. A compact policy, stated once, is enough — adapt this one:

```text
For requests to answer, explain, review, diagnose, or plan: inspect the relevant
materials and report the result; do not implement changes unless asked.
For requests to change, build, or fix: make in-scope local changes and run
non-destructive validation without asking first.
Require confirmation for external writes, destructive actions, or a material
expansion of scope.
```

Name the safe local actions explicitly (read files, inspect logs, edit in-scope code, run tests). Do not scatter "ask first" or "do not mutate" reminders — repetition triggers needless approval requests.

## Verification and stop rules

- Include one explicit check-your-work criterion: "run the affected tests and include the output".
- For code changes, require the most relevant validation available: targeted tests for the changed behavior, type or lint checks, a build of the affected packages.
- Bound loops: "stop when <condition>; retry transient failures at most N times; do not repeat completed side-effecting calls".
- When a lookup can come back empty or partial, ask for one or two meaningful fallbacks before concluding that no result exists.
- Missing evidence means a structured failure, not a guess: "if you cannot establish X, stop and report what is missing".
- Say which ambiguities warrant a question back and which the model may resolve itself.

## Task-type notes

- Long-running runs: ask for a short preamble before the first action and sparse, outcome-based updates at phase changes ("one concrete outcome and the next step") — not narration of every tool call.
- Plan deliverables: require requirements, named files or resources, state transitions or data flow, validation checks, failure behavior, security/privacy considerations, and the open questions that materially affect implementation.
- Frontend work: require inspecting and preserving existing design tokens, components, and patterns, and rendering the artifact before finalizing — checking layout, clipping, spacing, and visual consistency.
- Research and grounded answers: set a search budget (start with one broad, discriminative search; search again only for a missing required fact, requested exhaustiveness, or an otherwise unsupported claim) and a citation scope. Forbid invented names, metrics, dates, and outcomes.

## Model and effort choice

| Variant | Use for |
| --- | --- |
| `gpt-5.6-sol` | frontier capability, the hardest work |
| `gpt-5.6-terra` | balance of intelligence and cost |
| `gpt-5.6-luna` | efficient, high-volume workloads |

- Reasoning effort spans `none`–`max`. Migrating from 5.5/5.4: keep the old setting as the baseline, then test one level lower — 5.6 usually holds quality with fewer tokens. Reserve `max` for quality-first work and compare it against `xhigh` before adopting.
- Pro mode (`reasoning.mode: "pro"`, Responses API) applies more model work for a single high-stakes answer. Keep the same outcome-first prompt — never write "think harder" or "generate several candidates".
- Effort and mode belong in config or API parameters, not in prompt prose.

## Migrating a 5.5/5.4-era prompt

- Delete XML block-stacks and step-by-step process recipes; replace with the skeleton above.
- Drop bare "be concise" — 5.6 is already concise, and broad brevity lines can cut required content. If a short answer matters, list what it must preserve (conclusion, evidence, caveats, next action) and what to trim first; use `text.verbosity` for API defaults.
- Replace tone labels ("friendly") with concrete writing choices ("state the answer directly; acknowledge a reported problem before the next step").
- Keep what still works: one task per run, output contract, explicit verification, missing-evidence stop rules.
- Security-adjacent work (code review, vulnerability analysis, patching): state the defensive purpose and authorization up front. GPT-5.6 runs real-time cyber/bio misuse classifiers that can pause or block work that looks dual-use — occasionally including legitimate work.
- API-level features (Programmatic Tool Calling, persisted reasoning, explicit caching, multi-agent) are integration choices, not prompt text; see the official guide.

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
- If the root cause is outside `src/webhooks/`, stop and report instead of
  expanding scope.

## Output
A focused diff plus a three-line summary: cause, fix, evidence.
```
