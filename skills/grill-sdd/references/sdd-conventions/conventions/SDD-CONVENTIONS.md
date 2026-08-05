<!-- sdd-conventions-template v1.3.0 -->
## SDD conventions — shared mechanics

Shared structural rules for SDD-stage repositories, vendored from
`selfos-skills`. Product rules, phase plans, commands, privacy classes,
lanes, and review policy stay local to each repository.

- **Stable section numbers.** A top-level § number never changes meaning:
  no renumbering, and a retired number is never reused.
- **Stable rule ordinals.** Ordinals inside a §'s numbered rule lists are
  cited anchors exactly like § numbers: never renumbered, merged, split,
  or mid-inserted, and an ordinal never changes meaning. A new rule
  appends at the end of its list; a retired ordinal is never reused.
- **Map plus one file per section.** `SDD.md` is the map. Where the spec is
  split, each top-level § lives in its own `spec/NN-*.md` file.
- **Map lines are routers.** Each map index line carries its §'s role, the
  few terms that distinguish it from its neighbors, and the name of any
  authored canon artifact the § owns — at most 250 characters. The line
  changes only when that routing content goes stale (the role, a
  distinguishing term, or the owned-artifact set), not on every § edit.
- **Point reads by default.** Read only the §§ named by the task; a full
  pass over the spec happens only on an explicit full-pass request.
- **One normative home per rule.** Every rule is owned by exactly one §;
  everywhere else references it instead of restating it.
- **Enumerable data lives in canon artifacts.** Eval cases, enum tables,
  fixture examples, and machine-readable schemas are authored as canon
  artifacts (a ledger, schema files, fixture trees), CI-validated where a
  validator exists — a missing validator defers the check, never the
  extraction; the owning § keeps the annotation, the binding rule, and
  the pointer. Decisions, invariants, and rationale stay in the §§ in
  full text, and canon never points at living implementation code as its
  source.
- **A decision lands as three writes.** An accepted decision = the SDD edit,
  one concise Decision Log line, and the rationale in the issue or commit.
- **Decision Log entries are one or two sentences.** Sentence one states
  the decision; the second, where one exists, the rejected alternative
  with its reason. Detailed argument lives in the issue, the commit body,
  or the § edit; the vendored lint binds the length.
- **Decisions land at property altitude.** A ratified mechanism-level
  decision — a concrete sort key, a message text, a serialized-field
  list — enters the spec as the property or invariant it guarantees; the
  mechanism itself lives in code and its tests, and the rationale is one
  Decision Log line. No § accumulates mechanism essays — this covers
  every §, not a named list.
- **Unloading by maturity.** Once merged code and offline tests enforce
  a §'s mechanics, that § gets an unloading PR: the property stays in
  the § (or moves to the repository's invariants §), the mechanism text
  is deleted, and the "why" goes to the Decision Log. Retiring follows
  the stable-section-numbers rule; nothing is renumbered.
- **Correction versus trade-off.** A factual or editorial fix whose desired
  state existing canon already determines may be proposed as a correction;
  everything else is an owner trade-off and needs the owner's decision.
- **No silent bends.** Implementation never quietly deviates from the SDD;
  observed friction becomes an issue, and the SDD changes only through an
  accepted decision.
- **Findings live in issues.** Review findings and open questions go to
  GitHub issues, never to committed report files.
- **Invented data only in public repositories.** Examples and fixtures carry
  no real personal data, credentials, or local agent/tool state.
