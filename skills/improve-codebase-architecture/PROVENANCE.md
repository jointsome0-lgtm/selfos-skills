# Provenance — skills/improve-codebase-architecture

## skills/improve-codebase-architecture/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/improve-codebase-architecture/SKILL.md` |
| Blob | `b56969e92f0705d70700f908b8ec929a1edfa782` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations — the explore → HTML report → grilling process, the
friction checklist, the report card contract, and the side-effect rules are
otherwise preserved:

1. **Catalog placement and portable metadata added** — the upstream skill is
   placed at canonical `skills/improve-codebase-architecture/`; its
   description is rewritten in third person with a "Use when" clause, and
   local license, compatibility (naming the CDN network requirement),
   `metadata.selfos.version`, and `selfos.explicit-only` fields are added.
   Upstream's `disable-model-invocation: true` is kept.
2. **Skill invocations become bundled references** — upstream runs
   `/codebase-design` and `/grilling` as host slash-commands; here both are
   bundled dependencies read at `references/codebase-design/` and
   `references/grilling/`, so the workflow is self-contained on hosts
   without those skills installed.
3. **`CONTEXT.md` replaced by repository terminology** — upstream requires a
   `CONTEXT.md` domain glossary (created lazily during the grilling loop);
   the adaptation draws the project's domain terminology from its SDD,
   specs, or code, maintained by the ecosystem's `domain-modeling` skill
   where installed, introducing no domain-document requirement (same
   substitution as the `codebase-design` adaptation).
4. **ADRs replaced by the SDD Decision Log** — upstream reads `docs/adr/`
   and offers to record rejections as ADRs; the adaptation reads the
   project's SDD Decision Log and offers Decision Log entries instead, with
   the same reopen-only-when-friction-warrants rule for conflicting
   candidates.
5. **Sub-agents made harness-optional** — upstream mandates "use the Agent
   tool with `subagent_type=Explore`" and the design-it-twice "parallel
   sub-agent pattern"; the adaptation uses parallel sub-agents where the
   harness has them and sequential focused passes otherwise, removing
   harness-specific "Agent tool" wording.
6. **Recommendation-only scope capsule added** — new prose with no upstream
   counterpart: exploration and the report are read-only (the report file in
   the OS temp directory is the only written artifact); candidates are
   recommendations and implementation requires a separate explicit user
   request; grilling-loop side effects land only as owner-confirmed
   domain-model or Decision Log updates; repository-derived text is
   untrusted data whose embedded directives are never acted on.
7. **Host-specific upstream config not imported** — upstream's `agents/`
   host configuration directory is omitted; invocation posture is carried by
   the portable frontmatter instead.
8. **Report file creation hardened** — upstream resolves `$TMPDIR` with a
   `/tmp` fallback and a predictable `architecture-review-<timestamp>.html`
   name; the adaptation uses the host runtime's canonical temp-directory
   facility, an unguessable `<timestamp>-<random>` name with exclusive
   creation and owner-only permissions where supported, and an
   outside-the-repository check before opening (same rules as the `handoff`
   skill's temporary-file contract).

## skills/improve-codebase-architecture/HTML-REPORT.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/improve-codebase-architecture/HTML-REPORT.md` |
| Blob | `17f6d2c7b8342ee7c4260d8d98024d462c7d3eaa` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations — the scaffold, card contract, diagram patterns,
style guidance, and tone rules are otherwise verbatim upstream text:

1. **ADR callout becomes a Decision Log callout** — the card's conflict line
   cites the contradicted Decision Log entry instead of an ADR.
2. **`/codebase-design` skill references become bundled-reference links** —
   the three mentions of the `/codebase-design` skill point at
   `references/codebase-design/SKILL.md`.
3. **Mermaid locked to strict security mode** — upstream's scaffold sets
   `securityLevel: "loose"`; the adaptation sets `strict` and adds a rule to
   escape repository-derived text before interpolating it into diagrams,
   because diagram labels come from untrusted repository data.

## Bundled reference provenance

- `references/codebase-design/PROVENANCE.md`
- `references/grilling/PROVENANCE.md`

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
