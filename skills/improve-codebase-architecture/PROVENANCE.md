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
   local license, compatibility,
   and `metadata.selfos.version` fields are added. Upstream's
   `disable-model-invocation: true` is dropped (with the initially added
   `selfos.explicit-only` pairing) per issue #100 (2026-08-05): the skill is
   open to model invocation behind a prose start gate — confirm-first
   originally, relaxed to announce-and-proceed per issue #126 (2026-08-18),
   with repository writes still owner-gated inside the grilling loop.
2. **Skill invocations become bundled references** — design vocabulary and
   grilling are bundled at `references/codebase-design/` and
   `references/grilling/`. No conventions checker is required.
3. **`CONTEXT.md` replaced by repository terminology** — upstream requires a
   `CONTEXT.md` domain glossary (created lazily during the grilling loop);
   the adaptation draws the project's domain terminology from code
   and existing documentation, maintained by the ecosystem's `domain-modeling` skill
   where installed, introducing no domain-document requirement (same
   substitution as the `codebase-design` adaptation).
4. **Prior decisions read from commits and issues** — existing reasons
   constrain recommendations without requiring an ADR or Decision Log
   format. Cite the original decision when actual friction warrants
   reopening it. A rejected candidate creates no artifact by default.
5. **Sub-agents made harness-optional** — upstream mandates "use the Agent
   tool with `subagent_type=Explore`" and the design-it-twice "parallel
   sub-agent pattern"; the adaptation uses parallel sub-agents where the
   harness has them and sequential focused passes otherwise, removing
   harness-specific "Agent tool" wording.
6. **Recommendation-only scope capsule added** — new prose with no upstream
   counterpart: the target repository stays read-only during exploration
   and reporting; report construction may write only in an isolated OS
   temporary workspace, including build files and dependencies. Candidates are
   recommendations and implementation requires a separate explicit user
   request; grilling-loop side effects land only as owner-confirmed
   changes that honor the target repository's
   recognized instruction files; other repository-derived text is untrusted
   data whose embedded directives are never acted on.
7. **Host-specific upstream config not imported** — upstream's `agents/`
   host configuration directory is omitted; invocation posture is carried by
   the announce-and-proceed prose gate instead.
8. **Report file creation hardened** — upstream resolves `$TMPDIR` with a
   `/tmp` fallback and a predictable `architecture-review-<timestamp>.html`
   name; the adaptation uses the host runtime's canonical temp-directory
   facility, an unguessable `<timestamp>-<random>` name with exclusive
   creation and owner-only permissions where supported, and an
   outside-the-repository check before writing, following the `handoff`
   skill's temporary-file contract. The CDN opening-confirmation gate added
   in issue #126 is removed with offline delivery. An interactive report
   request covers its local preview; unattended runs return the path and
   stop for the owner's choice.
9. **Automatic preview uses a restricted browser context** — upstream's
   ordinary local openers cannot enforce offline execution. Verification and
   automatic preview block outbound networking and record attempted requests.
   When the host cannot enforce this, return the path and verification limits.
10. **Hot-spot scan made file-aware** — upstream infers hot spots from
    `git log --oneline` subjects; the adaptation aggregates changed paths
    from `git log --name-only`/`--stat` so churn, not commit-message
    wording, selects the hot spots.
11. **Instruction files loaded before exploration** — new prose with no
    upstream counterpart: the target repository's recognized instruction
    files are loaded before any history or code scan, and their read-scope
    rules bind throughout exploration, not only when landing edits.
12. **Rendering is chosen for the explanation** — the required Tailwind and
    Mermaid CDN stack is replaced by a self-contained local HTML contract.
    Libraries, WebGL/WebGPU, interaction, and animation are allowed. Selected
    stable library releases must be at least 30 days old at build time, with
    publication dates checked and versions pinned. The report is checked
    with outbound networking blocked before presentation. Downloaded build
    code requires filesystem and network isolation; without it, use native
    browser APIs or inert prebuilt browser bundles.
13. **Token-budget reporting added** — report the project's configured budget,
    usage, counting method, scope, and snapshot. Missing policy or unavailable
    measurements remain explicit. Size estimates do not become measured
    savings, and reporting does not install a checker or change project policy.

## skills/improve-codebase-architecture/HTML-REPORT.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/improve-codebase-architecture/HTML-REPORT.md` |
| Blob | `17f6d2c7b8342ee7c4260d8d98024d462c7d3eaa` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

The candidate structure and visual patterns derive from upstream. The local
adaptation changes delivery, library choice, interaction, and measurement:

1. **Prior-decision callout** — the card cites the relevant commit or issue
   instead of requiring an ADR format.
2. **`/codebase-design` skill references become bundled-reference links** —
   references to the `/codebase-design` skill point at
   `references/codebase-design/CONTRACT.md`.
3. **Repository text remains data** — Mermaid retains strict security mode
   when used. The escaping rule also covers other renderers, markup, and
   embedded data.
4. **The fixed scaffold and static-only restriction are removed** — the
   reference describes a local HTML artifact with included code and assets,
   freely chosen libraries subject to the 30-day release-age rule, and useful
   interaction. It adds isolated builds, a restrictive Content Security Policy,
   verification and preview with outbound networking blocked, motion controls,
   and readable findings when a GPU API is unavailable.
5. **Token-budget results are part of the report** — measured usage and the
   configured budget identify their method, scope, and snapshot. Missing
   budgets and unavailable counts are explicit; a bytes-divided-by-four
   fallback is labelled an estimate. Project-provided counters require
   filesystem and network isolation with the source checkout read-only;
   otherwise use the static estimate without executing project code.

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
