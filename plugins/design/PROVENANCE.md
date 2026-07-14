# Provenance — plugins/design

## skills/codebase-design/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/codebase-design/SKILL.md` |
| Blob | `16620c24528b737408e78d95dd6a0e01a98d3d63` |
| Imported | 2026-07-14 |
| License | MIT (notice below) |
| Status | **adapted** |

Named deviations — the glossary, diagrams, principles, testability rules,
relationships, and rejected framings are verbatim upstream text:

1. **Frontmatter description reworded** — upstream's "Shared vocabulary for
   designing deep modules." fails this repository's third-person index rule;
   the summary is rewritten ("Defines the shared deep-module design
   vocabulary …") and upstream's "Use when …" triggers are kept verbatim.
2. **Sub-agents made harness-optional** — the "Going deeper" pointer to
   DESIGN-IT-TWICE.md replaces upstream's "spin up parallel sub-agents" with
   parallel-where-supported, sequential-independent-passes otherwise.

## skills/codebase-design/DEEPENING.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/codebase-design/DEEPENING.md` |
| Blob | `3938457b88ddf98262d5f461aac703dbd74f749a` |
| Imported | 2026-07-14 |
| License | MIT (notice below) |
| Status | **verbatim** (byte-identical to the pinned blob) |

## skills/codebase-design/DESIGN-IT-TWICE.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/codebase-design/DESIGN-IT-TWICE.md` |
| Blob | `49a7c42a2ccc6aff0ffc09efd28e6a4aa3c373d7` |
| Imported | 2026-07-14 |
| License | MIT (notice below) |
| Status | **adapted** |

Named deviations — the process shape, the four design constraints, the
output schema, and the present-and-compare rules are otherwise preserved:

1. **Parallel sub-agents made optional** — upstream mandates "Spawn 3+
   sub-agents in parallel using the Agent tool"; the adaptation produces 3+
   independent designs via parallel sub-agents where the harness has them,
   or the same briefs as sequential independent passes in fresh contexts.
   Harness-specific "Agent tool" wording is removed; "Agent N" labels become
   "Design N".
2. **`CONTEXT.md` replaced by repository terminology** — upstream briefs
   include "CONTEXT.md vocabulary"; the adaptation draws the project's
   domain terminology from its SDD, specs, or code, introducing no domain
   document requirement.
3. **Brief injection boundary added** — new prose with no upstream
   counterpart: each brief is self-contained (restates the user's goal and
   binding constraints), and repository-derived material is untrusted
   data — neutral paraphrased facts and terms only, in a delimited data
   section; embedded directives, permission claims, links, and
   confirmations are never copied through or acted on.
4. **Recommendation-only scope capsule added** — new prose with no
   upstream counterpart: every design pass is read-only and returns only
   the five-field output; no file edits, mutating commands, staging,
   commits, publishing, fetching, secrets, or scope-widening; operational
   verbs in the reference documents recommend changes, never authorize
   them — implementation requires a separate explicit user request.

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
