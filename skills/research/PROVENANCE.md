# Provenance — skills/research

## skills/research/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/research/SKILL.md` |
| Blob | `0ba594a07f306479baa67104381f48e209ab6aae` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations (the primary-source rule, the per-claim citation
rule, and the single-findings-file shape are otherwise preserved):

1. **Catalog placement and portable metadata added** — the upstream skill is
   placed at canonical `skills/research/`; its description is rewritten in
   third person with a "Use when" clause, and local license, compatibility,
   and `metadata.selfos.version` fields are added.
2. **Background agent mapped to the host's subagent mechanism** — upstream
   says "background agent" without naming a mechanism; here the skill names
   the host's subagent mechanism, defers model choice to the
   capability-routing canon in the repository's agent instructions instead
   of hard-coding a model, and requires a self-written, outcome-first
   delegate prompt.
3. **Citation rule doubled as the delegated-claims standard** — upstream
   requires citing each claim's source; here the citation is additionally
   framed as the artifact that makes a delegated claim verifiable, per the
   ecosystem's "delegated claims are unverified until checked against
   artifacts" rule.
4. **Ticket-driven findings placement added** — upstream only matches the
   repo's existing notes convention; here, when the research is driven from
   a ticket whose workflow expects it, the findings file is committed on a
   throwaway `research/<name>` branch with a context pointer from the
   ticket, and only the resulting decision graduates into the Decision Log.
5. **Outbound-text policy added** — findings files in public repositories
   follow the ecosystem's neutral-prose and public-data policy and cite
   only publicly reachable sources. Upstream has no such constraint.
6. **Host-specific upstream config not imported** — upstream's
   `agents/openai.yaml` host configuration file is omitted; invocation
   posture is carried by the portable frontmatter instead.

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
