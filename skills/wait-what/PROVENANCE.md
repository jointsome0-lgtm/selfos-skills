# Provenance — skills/wait-what

## skills/wait-what/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/productivity/wait-what/SKILL.md` |
| Blob | `d493cfa883645bb7ce2e12f5232c0fbe3a0b9f87` |
| Imported | 2026-08-06 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations:

1. **Catalog placement and portable metadata added** — the upstream skill is
   placed at canonical `skills/wait-what/`; its description is rewritten in
   third person with a "Use when" clause, and local license, compatibility,
   and `metadata.selfos.version` fields are added.
2. **Explicit-only invocation kept and made portable** — upstream's
   `disable-model-invocation: true` is retained and paired with
   `metadata.selfos.explicit-only: "true"` per catalog conventions. The
   top-level field is enforced by Claude Code only, and the metadata key
   only by this repository's tooling; the portable guard for other hosts
   is the body's explicit-request prose, added in this import.
3. **Terms source generalized** — upstream's reference to a repository
   `CONTEXT.md` is replaced with the ubiquitous language from the
   repository's SDD or domain-model document when one exists, falling back
   to plain jargon-free wording, keeping the skill portable across
   repositories (owner decision, 2026-08-06).
4. **STE reference kept by name** — the ASD-STE100 Simplified Technical
   English requirement is preserved as a named-spec reference; its rules are
   deliberately not paraphrased into the skill body (owner decision,
   2026-08-06).
5. **Voice converted from prompt to instruction** — the upstream body is a
   first-person message addressed to the agent ("Wait — I don't understand
   …"); the imported body restates the same contract as instructions to the
   agent, matching the catalog's skill format.
6. **Scope boundary added** — the skill restates the previous message only;
   it explicitly does not advance the work, edit files, or make decisions.

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
