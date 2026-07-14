# Provenance — plugins/sdd

## skills/slice/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/to-tickets/SKILL.md` |
| Blob | `23140c577f71c98993523f0dbec74f250561b708` |
| Imported | 2026-07-14 |
| License | MIT (notice below) |
| Status | **adapted** |

Named deviations from the upstream text — the tracer-bullet rules, blocking
edges, expand–migrate–contract sequencing, frontier discipline, dependency-order
publication, stale-snippet rule, and the ticket-template skeleton preserve
upstream behavior:

1. **Tracker fixed to GitHub issues** — upstream's `/setup-matt-pocock-skills`
   configuration step, the local-file tracker mode (`.scratch/<slug>/issues/`),
   and the `ready-for-agent` triage label are removed; selfos repositories keep
   GitHub issues as the active-work system.
2. **Owner interview replaced** — upstream's "Quiz the user" step becomes the
   shared `grilling` primitive (declared plugin dependency), one decision at a
   time with a recommendation each; no second interview loop is kept in this
   skill.
3. **Scope contract added** — upstream accepts "a plan, spec, or conversation";
   `slice` takes exactly one implementation-ready SDD §, phase, or approved
   parent issue, verifies readiness under repository canon, and refuses with
   the precise readiness blocker otherwise.
4. **SDD read-only rule** — a contradiction or missing decision found while
   slicing becomes a proposed spec-issue draft, never a ticket assumption or a
   spec edit; upstream has no spec-authority boundary.
5. **Canon vocabulary** — upstream's domain glossary and ADR references are
   replaced by SDD-defined terms, Decision Log entries, and the shared
   conventions surface.
6. **Prefactoring narrowed** — upstream's general prefactor invitation becomes:
   horizontal scaffolding only when it genuinely gates vertical behavior, and
   then as an explicit blocker ticket.
7. **Ticket schema extended** — tickets additionally declare the repository and
   Track A/B lane, the SDD § and parent-issue citations, verification, the end
   artifact, the privacy/public-data boundary, and the rejected alternative
   when a design choice is embedded.
8. **Publication gate hardened** — upstream publishes after breakdown approval;
   `slice` publishes only after the primitive's final confirmation, a
   non-interactive run creates nothing, and claim-before-implementation (by
   issue assignment) is added to the frontier rule.

`skills/slice/EXAMPLES.md`, `skills/grill-sdd/`, `conventions/`, and `scripts/`
are local content, not vendored.

## Upstream license notice

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
