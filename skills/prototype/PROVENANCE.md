# Provenance — skills/prototype

## skills/prototype/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/prototype/SKILL.md` |
| Blob | `e75d5331ceffd9b2c5a9554c3db124d848afa054` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations (both prototype branches — logic and UI — and the
shared rules are otherwise preserved):

1. **Catalog placement and portable metadata added** — the upstream skill is
   placed at canonical `skills/prototype/`; its description is rewritten in
   third person with a "Use when" clause, and local license, compatibility,
   and `metadata.selfos.version` fields are added.
2. **Capture rules rewritten to the ecosystem's worktree convention** —
   upstream commits the finished prototype to an unspecified throwaway branch
   after the fact; here all prototype work happens from the start on a
   throwaway branch checked out in a `<repo>/.worktrees/<name>` worktree,
   never the primary checkout. Only the validated decision lands on main
   through the normal change process; the branch is pushed and kept as the
   primary source, and the worktree is removed afterwards.
3. **Context pointer made mandatory and structured** — upstream leaves "a
   context pointer to that branch on the implementation issue"; here the
   comment on the driving issue must name the prototype branch, the question
   it settled, and the verdict.
4. **Outbound-text policy added** — issue comments and commit messages follow
   the ecosystem's neutral-prose and public-data policy (invented examples
   only; no personal data, credentials, private paths, or local agent state).
   Upstream has no such constraint.
5. **Host-specific upstream config not imported** — upstream's
   `agents/openai.yaml` host configuration file is omitted; invocation
   posture is carried by the portable frontmatter instead.

## skills/prototype/LOGIC.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/prototype/LOGIC.md` |
| Blob | `fe9a2c29f77b9b7182ad7fa4bd251f27e506b7d9` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations: the process, module-shape guidance, TUI contract,
and anti-patterns are preserved verbatim; only step 7 (capture) is reworded to
match the SKILL.md capture rules above — the validated logic module lifts into
the real code on main, the TUI shell stays with the prototype on its throwaway
worktree branch, and the driving issue carries the pointer.

## skills/prototype/UI.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/prototype/UI.md` |
| Blob | `76c0f6012b016af04d6105fa696a9a0e29dfa53a` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations: sub-shapes, process, switcher contract, and
anti-patterns are preserved verbatim; only step 6 (capture and clean-up) is
reworded to match the SKILL.md capture rules above — the winning variant folds
into main, the full variant set and switcher stay on the throwaway worktree
branch (upstream instead deletes them from main after committing the branch),
and the driving issue carries the pointer.

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
