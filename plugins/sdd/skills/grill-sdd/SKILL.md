---
name: grill-sdd
description: Relentless interview over named sections of this repository's SDD to stress-test decisions and invariants. Use when the user asks to grill the SDD, grill invariants, or stress-test a spec section.
---

Grill the user relentlessly about the named SDD section(s) until you reach a shared understanding. Self-contained adaptation of the generic grilling discipline for SDD-stage repositories.

## Interview discipline

- Ask one question at a time; wait for the answer before the next. Multiple questions at once are bewildering.
- For every question, give your recommended answer.
- Walk each branch of the design tree, resolving dependencies between decisions one by one.
- If a question can be answered from the repository (SDD, code, issues), answer it yourself instead of asking.

## SDD-specific rules

- Read only the sections in scope. In a split spec (`SDD.md` map + `spec/`, one file per §), a section = its file under `spec/`; in a monolithic `SDD.md`, locate the § via the index and read only that range. Never load the whole spec into context.
- Stress-test invariants with concrete scenarios that probe edge cases and force precise boundaries.
- Challenge terms against the SDD's own definitions; when usage drifts from the defined term, call it out immediately.
- Every grilled point must land before the session ends:
  - resolved → edit the SDD in place and add one Decision Log line;
  - unresolved or deferred → file an issue in this repository.
- Create no other artifacts: no report files, no CONTEXT.md, no ADRs. The SDD is the single durable artifact; issues hold the ephemeral.
