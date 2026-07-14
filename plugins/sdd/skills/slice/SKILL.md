---
name: slice
description: Slices one implementation-ready SDD section, phase, or approved parent issue into dependency-ordered vertical GitHub issues — tracer-bullet tickets carrying SDD citations, the Track A/B lane, acceptance criteria, verification, blocking edges, and the end artifact, drafted with the shared grilling loop and published only after owner confirmation. Use when the user asks to slice a spec section, phase, or parent issue into tickets, or to turn an approved SDD scope into implementation issues.
disable-model-invocation: true
---

Turn exactly one implementation-ready scope — a named SDD §, phase, or approved parent issue — into a dependency-ordered set of vertical GitHub issues. This skill drafts the ticket graph; owner choices about seams, granularity, and blocking edges are resolved through the shared `grilling` decision primitive from the `decision` plugin, and publication happens only after the owner's final confirmation.

Resolving the primitive: installed, it is the `grilling` skill (`/decision:grilling`) — this plugin's manifest declares the `decision` dependency; in a bare repository checkout, follow the `grilling` row of the repository's `AGENTS.md` index. Never substitute a local paraphrase of the interview loop.

## Resolve canon first

- Read the repository's `AGENTS.md`, the SDD map, only the referenced § files, the Decision Log entries and open issues that bear on the scope, the parent issue, and the nearby implementation and tests.
- Verify the named scope is implementation-ready under current repository canon — a handoff document or a date cannot silently freeze it. If it is not ready, refuse to slice and name the precise readiness blocker: the undecided §, the missing decision, or the contradiction.
- The SDD is read-only inside slicing: a contradiction or missing decision becomes a proposed spec-issue draft, never an invented ticket assumption. Section mechanics follow the repository's embedded SDD-conventions block — fallback: [`../../conventions/SDD-CONVENTIONS.md`](../../conventions/SDD-CONVENTIONS.md).

## Draft tracer bullets

- Each ticket cuts a narrow but complete path through every necessary layer and is demoable or independently verifiable on its own — vertical, never a horizontal slice of one layer.
- Each ticket fits one fresh implementation session and names the concrete owner-visible or executable artifact that exists when the session ends.
- Horizontal scaffolding is allowed only when it genuinely gates vertical behavior, and then as an explicit blocker ticket.
- Wide mechanical changes are never forced into fake vertical slices: sequence them **expand–migrate–contract** — expand the new form beside the old, migrate call sites in blast-radius-sized batches (each batch its own ticket blocked by the expand), contract by deleting the old form in a final ticket blocked by every batch.
- Avoid file paths and code snippets in tickets — they go stale. Exception: a prototype-derived snippet that encodes a decision more precisely than prose (schema, state machine, type shape), trimmed to the decision-rich part and marked as prototype output.

## Carry ecosystem constraints — every ticket declares

- the repository and its **Track A or Track B** lane, obeying that repository's lane rules;
- the SDD § and the parent issue it implements — citations, not restatements;
- the delivered behavior, acceptance criteria, verification (how the artifact is exercised), blocking edges, and the privacy/public-data boundary it must respect;
- the rejected alternative with its reason, when the ticket embeds a design choice;
- the end artifact that exists when the implementation session ends.

Tickets cannot silently edit or bend the SDD. Implementation friction becomes a separate issue and blocks a slice only when canon truly blocks it.

## Use the shared decision loop

- Present the proposed seams, granularity, blocking edges, and merge/split options with a recommendation each; then follow the `grilling` primitive one decision at a time. Accepted, rejected, deferred-with-trigger, and blocked-by-missing-fact are all valid ends for a branch.
- Publish tickets and spec-friction issues only after the owner's final confirmation of the whole graph.
- In a non-interactive run, output the proposed ticket graph and the issue drafts and create or edit nothing — filing an issue is action, not note-taking.

## GitHub execution model

- Publish blockers first, in dependency order, so later tickets reference real issue numbers; use the tracker's native blocking relation where one exists, otherwise a "Blocked by" list of real references.
- The frontier is: open, all blockers closed, unclaimed. Claim a ticket before implementing by assigning the issue when the tracker supports it.
- One ticket per implementation session, clearing context between tickets.
- Never close or rewrite the parent issue.

## Session outcome discipline

Every ticket states its repository, Track A/B lane, verification, and end artifact. This outcome discipline is deliberately a checked invariant of the ticket schema — keep the four fields present and exact, so any later evaluation of a separate session-preflight step stays possible against real tickets.

## Ticket template

```markdown
## Parent

<parent issue reference> — implements <SDD § reference>

## Delivered behavior

The end-to-end behavior this ticket makes work, from the owner's perspective.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Verification

How the end artifact is exercised: the command, demo path, or test run.

## End artifact

What exists and is observable when the implementation session ends.

## Lane

Repository: <repository> — Track A|B. Privacy: <the public-data boundary this ticket must respect>.

## Blocked by

- <real issue references>, or "None — frontier".

## Rejected alternative

<alternative — reason> (only when this ticket embeds a design choice)
```

Worked examples: [EXAMPLES.md](EXAMPLES.md).
