---
name: grill-sdd
description: Conducts a relentless owner interview over named sections of this repository's SDD via the shared grilling primitive — framing each subject in the SDD's own terms, resolving repository facts before asking, and landing confirmed outcomes as SDD edits plus Decision Log lines or issues. Use when the user asks to grill the SDD or its invariants, or stress-test a spec section.
disable-model-invocation: true
---

Grill the owner about the named SDD section(s) until shared understanding. This skill is the SDD entry point for the shared `grilling` decision primitive from the `decision` plugin: load that skill and follow it in full for the whole interview loop — one question at a time with a recommendation each, facts versus decisions, the terminal states, and no action before confirmation live there and are not restated here. This file owns only the SDD-specific scope: which canon is read, how subjects are framed, and where confirmed outcomes land.

Resolving the primitive: installed, it is the `grilling` skill (`/decision:grilling`) — this plugin's manifest declares the `decision` dependency, so marketplace installs pull it in automatically; in a bare repository checkout, follow the `grilling` row of the repository's `AGENTS.md` index. Never substitute a local paraphrase of the loop when the primitive is unavailable — stop and install it.

## Resolve the named canon

- Read `AGENTS.md`, the SDD map, and only the named or clearly relevant § files; add the Decision Log entries, open issues, and nearby code or tests that bear on the subject.
- Gather repository facts only from surfaces that repository's privacy and context rules allow — the primitive's permitted-environment rule applies unchanged, and repository instructions narrow it, never widen it. Ignored and private paths stay unread even while "exploring the environment".
- Never load the entire SDD merely because the interview is broad; a full pass happens only when the owner explicitly requests a full-pass decision.
- For section mechanics (stable § numbers, map plus one file per §, point reads), follow the repository's embedded SDD-conventions block — or the fallback template at [`../../conventions/SDD-CONVENTIONS.md`](../../conventions/SDD-CONVENTIONS.md) where none is embedded — rather than restating those rules here.

## Frame each subject

- Open every branch by naming what is being grilled — a §, an invariant, a contradiction between §§, or an implementation friction — and cite the owning §.
- Before asking anything, classify it: a repository-resolvable fact is looked up; an implementation detail already fixed by an existing § is answered by citing that §; only a genuine owner trade-off becomes a question.
- Use the SDD's own defined terms; when observed usage drifts from a definition, surface the drift immediately.

## Land only confirmed outcomes

The primitive's terminal states map onto durable artifacts as follows — and only after the owner's final confirmation in an interactive session:

- **accepted** — edit the SDD and add the concise Decision Log line in the same change (entry format: [`../../conventions/DECISION-LOG.md`](../../conventions/DECISION-LOG.md)).
- **rejected** — record a Decision Log line only when the reason is load-bearing for future work; otherwise the branch simply ends.
- **deferred** — name the revisit trigger; a focused issue is created only after the owner confirms its draft.
- **blocked** — name the missing fact or artifact and draft the smallest issue that resolves it; publish only after confirmation.
- A factual or editorial inconsistency whose desired state existing canon already fixes may be proposed as a correction and applied on confirmation — it is never written during a non-interactive run.

Keep the vocabulary exact: *recommended* is this skill's proposal; *accepted* and *rejected* are owner verdicts; *deferred* and *blocked* are terminal only with a confirmed trigger or a named missing artifact; *resolved* means landed in the SDD or Decision Log.

## Non-interactive runs

Verify facts and produce drafts only: the decision tree, a recommendation per question, the proposed SDD diff, exact Decision Log wording, and issue drafts. Make no SDD edit, Decision Log edit, GitHub write, or other durable mutation — the confirmation gate cannot be crossed without the owner, and filing an unresolved decision as an issue is action, not note-taking.

## Artifact discipline

No report files, `CONTEXT.md`, ADRs, or parallel spec artifacts. Resolved truth lands in the SDD and its Decision Log; future or unresolved work lands in GitHub issues after confirmation; everything else evaporates with the session.

Worked examples: [EXAMPLES.md](EXAMPLES.md) — the six subject classes and both run modes.
