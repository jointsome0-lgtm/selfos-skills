# Provenance — skills/wayfinder

## skills/wayfinder/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/engineering/wayfinder/SKILL.md` |
| Blob | `e4984ed327e12ba65303f4b5de2eb75c01e99c16` |
| Imported | 2026-08-05 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations (the map/ticket model, fog of war, out-of-scope
rules, ticket types, one-ticket-per-session cadence, and both invocation
modes are otherwise preserved):

1. **Catalog placement and portable metadata added** — the upstream skill
   is placed at canonical `skills/wayfinder/`; its description is rewritten
   in third person with a "Use when" clause, and local license,
   compatibility, and `metadata.selfos.version` fields are added.
   Upstream's `disable-model-invocation: true` is dropped (with the
   initially added explicit-only pairing) per issue #100 (2026-08-05): the
   skill is open to model invocation behind a prose start gate —
   confirm-first originally, relaxed to announce-and-proceed per issue
   #126 (2026-08-18), with publication and repository writes still
   owner-gated inside the workflow.
2. **Tracker-doc dependency replaced with self-contained GitHub
   conventions** — upstream defers tracker operations to an external
   tracker doc provisioned by `/setup-matt-pocock-skills`, with a
   local-markdown fallback. Here the conventions and verified `gh`
   commands (native sub-issues, native blocked-by issue dependencies,
   assignee-as-claim, frontier query) live in the bundled
   [TRACKER.md](TRACKER.md); the local-markdown fallback is dropped and
   GitHub access is a declared compatibility requirement — an unreachable
   tracker stops the skill instead of degrading to a second store.
3. **Decisions linked to resulting commits** — the issue resolution records
   the decision and reason. When it changes the repository, that change
   lands first through the normal commit or PR flow; the commit explains
   why and references the ticket. Planning-only decisions need no empty
   commit. The map links resolutions; no separate Decision Log is required.
4. **Default destination named** — approved implementation-ready scope,
   handed to `slice` for ticketing the build. Other destinations remain
   legitimate when the map names them.
5. **Skill invocations narrowed** — grilling is bundled through
   `BUNDLE.json`; prototype is a sibling skill. Research tickets use primary
   sources directly and cite findings in the issue, without a separate
   skill, findings branch, or file. Domain-modeling is optional when the
   host provides it.
6. **Outbound-text policy added** — everything written to the tracker
   follows the ecosystem's neutral-prose and public-data policy; task
   resolutions never record credentials or private data on a public
   tracker. Upstream has no such constraint.
7. **Host-specific upstream config not imported** — upstream's
   `agents/openai.yaml` host configuration file is omitted; invocation
   posture is carried by the announce-and-proceed prose gate instead.

## Bundled reference provenance

The self-contained dependency copies retain their own upstream pins, import
dates, adaptation notes, and license notices:

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
