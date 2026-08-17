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
   #126 (2026-08-18), with publication and Decision Log writes still
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
3. **Decision store moved from tickets to the SDD Decision Log** —
   upstream records each answer as a resolution comment, making the ticket
   the decision's one home. Here a ticket resolves only when its decision
   has landed in the repository's SDD Decision Log through the repo's
   normal change flow (direct commit or pull request — the skill doesn't
   mandate which); the resolution comment quotes the landed entry verbatim
   and links the landing commit or pull request; the close comes only
   after the entry lands; and the map's Decisions-so-far index points into
   the repository, not at ticket comments. Each entry ends with the
   ticket's `#123` reference, which the Decision Log grammar already
   accepts. Rationale: issues are host data — not cloned, not backed up —
   while the log is versioned, reviewed, and greppable offline.
4. **Default destination named** — upstream leaves the destination fully
   open. Here it defaults to an implementation-ready SDD scope, with the
   finished map handing off to the `slice` skill for ticketing the build;
   other destinations remain legitimate but are named as departures.
5. **Skill invocations remapped to the catalog** — upstream invokes
   `/grilling`, `/domain-modeling`, `/research`, and `/prototype` as
   host-installed slash commands. Here the grilling contract and the SDD
   conventions (Decision Log grammar and lint) are bundled via
   `BUNDLE.json`; `research` and `prototype` are invoked as sibling
   catalog skills declared in `compatibility`; domain-modeling is invoked
   only when the host has such a skill installed, since this catalog does
   not ship one.
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
- `references/sdd-conventions/PROVENANCE.md`

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
