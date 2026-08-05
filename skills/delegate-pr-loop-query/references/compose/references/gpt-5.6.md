# GPT-5.6 family (gpt-5.6-sol / -terra / -luna, Codex runs)

Sources: OpenAI's [GPT-5.6 prompting guide](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6) and [GPT-5.6 model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6). Checked against upstream 2026-08-04.

Applies to `gpt-5.6-sol` (flagship; the `gpt-5.6` alias routes here), `gpt-5.6-terra` (balanced cost), `gpt-5.6-luna` (high-volume) — in the Codex CLI, Codex cloud, or the API. On conflict with the core skill, this file wins.

## Core principle: lean and outcome-first

Describe the outcome, not the procedure. In OpenAI's internal coding-agent evals, leaner prompts scored roughly 10–15% higher while cutting total tokens 41–66% and cost 33–67%. GPT-5.6 infers the intended level of work from context, so provide domain context, hard constraints, boundaries, and success criteria — do not prescribe every step.

- One task per run.
- State each instruction once; delete repeated rules and redundant examples.
- Turn process steps into success criteria: "tests X and Y pass", not "first run X, then run Y".
- Keep an example only when it encodes a real requirement or corrects a measured gap.
- Reserve ALWAYS/NEVER for true invariants (a binding AGENTS.md, do-not-touch files). Everything else reads better as a success criterion.
- For a one-off delegated task, the core skeleton (Goal / Context / Constraints / Success criteria / Output plus stop rules) is usually enough; Role and Personality sections earn their place in reusable agent instructions and customer-facing prompts.

## Tool strategy

- Expose only task-relevant tools. A tool description should state what the tool does, when to use it, the important return fields, and its error behavior.
- When correctness depends on prior lookups, say so: "before taking an action, resolve required discovery, retrieval, and validation steps".
- Parallelize independent reads; keep work sequential when one result determines the next action.
- Programmatic Tool Calling suits bounded filter/join/sort/aggregate/batch workflows: specify the bounded stage, eligible tools, output schema, retry limits, and handoff conditions — never a generic "use PTC efficiently". Prefer direct calls when one call suffices, outputs are small, each result changes the next decision, approval is needed, or citations must be preserved.

## Autonomy

GPT-5.6 is proactive and persistent on multi-step tasks; the core skill's compact autonomy policy is enough. Name the safe local actions explicitly (read files, inspect logs, edit in-scope code, run tests). Do not scatter "ask first" or "do not mutate" reminders — repetition triggers needless approval requests.

## Verification and stop rules

- Include one explicit check-your-work criterion: "run the affected tests and include the output". (Model-specific: on Claude Opus 5 the same instruction causes over-verification — see its reference.)
- For code changes, require the most relevant validation available: targeted tests for the changed behavior, type or lint checks, a build of the affected packages.
- When a lookup can come back empty or partial, ask for one or two meaningful fallbacks before concluding that no result exists.

## Personality and collaboration style

For customer-facing or reusable agent prompts, define these separately — they control different things:

- **Personality**: tone, warmth, directness, formality, humor, polish — the user-experience voice.
- **Collaboration style**: when the model asks questions vs makes assumptions, how much initiative it takes, whether it explains trade-offs, how it handles uncertainty.

Keep both short, describe concrete writing choices rather than broad labels ("state the answer directly; acknowledge a reported problem before the next step", not "friendly"), and never let them substitute for clear goals and success criteria.

## Task-type notes

- Long-running runs: ask for a short preamble before the first action and sparse, outcome-based updates at phase changes ("one concrete outcome and the next step") — not narration of every tool call. At the integration level: preserve assistant phase values when replaying history, compact after major milestones (not every turn) while keeping the prompt prefix stable, and use persisted reasoning only while objectives stay stable — stale reasoning adds tokens and anchors the model to an outdated approach.
- Plan deliverables: require requirements, named files or resources, state transitions or data flow, validation checks, failure behavior, security/privacy considerations, and the open questions that materially affect implementation.
- Frontend work: require inspecting and preserving existing design tokens, components, and patterns, no unrequested features, and rendering the artifact before finalizing — checking layout, clipping, spacing, and visual consistency.
- Vision and computer use: choose image detail intentionally — original detail only for large, dense, or coordinate-sensitive images where the extra cost and latency are justified.
- Research and grounded answers: set a search budget (start with one broad, discriminative search; search again only for a missing required fact, requested exhaustiveness, or an otherwise unsupported claim) and a citation scope; label inference separately from sourced claims and report conflicts rather than smoothing them over.
- Creative drafting from sources: distinguish source-backed facts from creative wording. In any grounded task, forbid invented names, metrics, dates, roadmap status, customer outcomes, and product capabilities — a draft never gets stronger by making things up.

## Model and effort choice

| Variant | Use for |
| --- | --- |
| `gpt-5.6-sol` | frontier capability, the hardest work |
| `gpt-5.6-terra` | balance of intelligence and cost |
| `gpt-5.6-luna` | efficient, high-volume workloads |

- Reasoning effort spans `none`–`max` at the API; apply the core skill's operating ladder (`low`–`high`, `medium` as the balanced default, `high` only when evals or task shape show a meaningful gain).
- Migrating from 5.5/5.4: keep the old setting as the baseline, then test one level lower — 5.6 usually holds quality with fewer tokens.
- Pro mode (`reasoning.mode: "pro"`, Responses API) applies more model work for a single high-stakes answer. Keep the same outcome-first prompt — never write "think harder" or "generate several candidates".
- Effort and mode belong in config or API parameters, not in prompt prose.

## Migrating a 5.5/5.4-era prompt

- Eval-driven, incrementally: switch the model with the prompt unchanged, run representative evals to get a baseline, then remove obsolete scaffolding and add only the smallest targeted fix per measured regression, re-running evals after each change. Never rewrite a working prompt stack all at once — you lose the ability to attribute a behavior shift to the model, the effort setting, the prompt, or the tool set.
- Delete XML block-stacks and step-by-step process recipes; replace with the core skeleton.
- Drop bare "be concise" — 5.6 is already concise, and broad brevity lines can cut required content. If a short answer matters, list what it must preserve (conclusion, evidence, caveats, next action) and what to trim first; use `text.verbosity` for API defaults.
- Keep what still works: one task per run, output contract, explicit verification, missing-evidence stop rules.
- Security-adjacent work (code review, vulnerability analysis, patching): state the defensive purpose and authorization up front. GPT-5.6 runs real-time cyber/bio misuse classifiers that can pause or block work that looks dual-use — occasionally including legitimate work.
- Remaining API-level features (persisted reasoning, explicit caching, multi-agent orchestration) are integration choices, not prompt text; see the official guide.
