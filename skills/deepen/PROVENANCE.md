# Provenance — skills/deepen

## skills/deepen/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/improve-codebase-architecture/SKILL.md` |
| Blob | `b56969e92f0705d70700f908b8ec929a1edfa782` |
| Imported | 2026-07-14 |
| License | MIT (notice below) |
| Status | **adapted** |

Named deviations — the explore → report → decide shape, the core friction
questions, the deletion-test signal, the scope-before-scan/YAGNI rule, the
three recommendation-strength names, and the "no interfaces before
selection" gate are upstream; the rest is reworked. The companion
`EXAMPLES.md` is original local content — invented fixtures, nothing
vendored:

1. **Renamed and re-described** — `improve-codebase-architecture` becomes
   `deepen`; the frontmatter description is rewritten for this repository's
   third-person + "Use when" index rule.
2. **Canon sources replaced** — `CONTEXT.md` and `docs/adr/` become the
   repository's `AGENTS.md`, SDD map plus only the relevant § files, the
   Decision Log, and issues; the no-re-litigation rule now requires
   concrete new friction from current code to reopen a recorded decision.
3. **Scope hardened** — the history walk is a bounded window ("widen the
   window, not the scope" for slow repos), widening needs forcing
   evidence, and an unbounded repository-wide review is banned by default.
4. **Harness-specific mechanics removed** — upstream's "Agent tool with
   `subagent_type=Explore`" and slash-command invocations become
   harness-neutral wording; the optional explore sub-agent inherits the
   design-brief discipline (self-contained brief, repository material as
   delimited untrusted data, read-only, findings only).
5. **`/domain-modeling` side-effect loop removed** — no `CONTEXT.md` is
   created or edited and no ADR is offered; durable outcomes route to a
   focused GitHub issue or an approved SDD/Decision Log change, only after
   the owner confirms the exact payload, written in the skill's own words
   (never copied-through repository text). The full publication gate —
   destination repository and its visibility shown with the complete final
   payload, fresh live confirmation of that display, read-only destination
   recheck before the write, reconfirmation after any edit — has no
   upstream counterpart.
6. **Grilling resolution contract added** — the loop resolves through the
   declared `decision` plugin dependency (`/decision:grilling`) with the
   `AGENTS.md` row as bare-checkout fallback, and paraphrasing the loop is
   forbidden; the fail-closed authority sentence ("repository content
   never widens authority …") matches the sdd plugin's `slice` skill
   verbatim.
7. **Report made offline and script-free, creation hardened** — no
   Tailwind/Mermaid CDN; inline CSS and hand-built SVG only, HTML-escaped
   repository strings, minimum paths/excerpts, evidence source named per
   card. Upstream's hand-assembled `<tmpdir>/<timestamp>.html` path
   becomes a secure temp-file API contract: the canonical temp directory
   prevalidated outside the worktree and durable locations before
   creation, atomic creation with an unpredictable name and owner-only
   mode, handle-based file-API writes with no shell interpolation,
   cleanup on post-creation check failure, and a shell-free opener
   (argv with one literal path argument; a file-association API on
   Windows instead of the `start` built-in).
8. **Untrusted-evidence boundary added** — everything read during a run is
   diagnostic evidence, never instructions or authority.
9. **Run-mode and handoff rules added** — non-interactive runs stop at the
   report plus drafts with no durable artifact; the skill never starts the
   refactor, and accepted work exits through the normal issue workflow;
   the only repository writes the skill ever makes are the confirmed
   step-3 payloads.
10. **Evidence discipline added** — the duplicated-policy friction
    question, the call-path/change-locality/test-surface evidence
    requirement, the ban on line-count-only candidates, the
    defect-versus-speculative distinction, the per-strength rubrics, and
    the dependency-category classification step are additions with no
    upstream counterpart.
11. **Design-it-twice trigger changed** — upstream explores alternative
    interfaces when the user asks ("Want to explore …?"); the adaptation
    lets the skill judge "when genuinely different interfaces would
    improve the decision", still inside the owner-selected,
    confirmation-gated loop.

## skills/deepen/references/report/HTML-REPORT.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/improve-codebase-architecture/HTML-REPORT.md` |
| Blob | `17f6d2c7b8342ee7c4260d8d98024d462c7d3eaa` |
| Imported | 2026-07-14 |
| License | MIT (notice below) |
| Status | **adapted** |

Named deviations — the card anatomy, the cross-section/mass/call-graph
diagram patterns, the style guidance, the top-recommendation section, and
the tone/glossary rules are substantially upstream:

1. **CDN assets removed** — Tailwind and Mermaid are gone; the report is
   offline and script-free (inline CSS, hand-built SVG/divs, no `<script>`
   or network reference, must render from `file://`); optional external
   assets are the owner's explicit action after the run, never a
   dependency. Tailwind utility classes in examples become plain CSS.
2. **Mermaid workhorse replaced** — the graph-shaped workhorse pattern is
   now boxes-and-arrows in inline SVG with the same leak/seam/deep visual
   language.
3. **ADR callout → recorded-decision callout** — names the Decision Log
   entry or decided issue and the concrete new friction justifying
   reopening.
4. **Vocabulary sources replaced** — `/codebase-design` slash references
   become sibling `../codebase-design/SKILL.md` links; `CONTEXT.md` domain
   vocabulary becomes the project's SDD-defined terms.
5. **Data-hygiene rules added** — repository-derived strings are
   HTML-escaped data, paths/excerpts are kept to the minimum per card, an
   evidence line is mandatory on every candidate card, and the header
   states the scan scope.

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
