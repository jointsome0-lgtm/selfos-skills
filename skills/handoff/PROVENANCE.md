# Provenance — skills/handoff

## skills/handoff/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/productivity/handoff/SKILL.md` |
| Blob | `043d9e13dc7eca3002a47d3ab9865c568f647863` |
| Imported | 2026-07-21 |
| License | MIT (notice below) |
| Status | **adapted** |

Named semantic deviations:

1. **Catalog placement and portable metadata added** — the upstream skill is
   placed at canonical `skills/handoff/`; its description is rewritten in
   third person with a "Use when" clause, and local license, compatibility,
   and `metadata.selfos.version` fields are added.
2. **Invocation posture made composable** — the upstream host-specific
   `argument-hint` and `disable-model-invocation` fields are removed. The
   optional focus remains part of the prose contract, and direct or declared
   composite invocation is explicitly supported.
3. **Output contract tightened** — the output is exactly one compact Markdown
   document created under the canonical OS temporary directory with an
   unpredictable `handoff-<timestamp>-<random>.md` name, exclusive creation
   and owner-only permissions where supported, post-write path/readability
   checks, and no repository or workspace mutation.
4. **Continuation context enumerated** — current goal, meaningful progress,
   unresolved blockers, and non-obvious decisions or constraints are required;
   only context unrecoverable from durable artifacts belongs in the handoff.
   Full transcripts, chain-of-thought, copied finding ledgers, and routine
   investigative detail are explicitly excluded.
5. **Durable-reference rule broadened** — paths or URLs may point to specs,
   plans, ADRs, issues, commits, diffs, and PR threads, with contents left in
   those artifacts instead of copied into the handoff.
6. **Privacy constraints strengthened** — credentials, keys, tokens,
   passwords, session identifiers, cookies, private keys, personal data, and
   other sensitive values are removed from prose and references, replaced by
   typed non-reversible redaction markers, and checked again before writing.
7. **Suggested-skill guidance made actionable** — the required `Suggested
   skills` section gives a reason for each focus-relevant recommendation and
   permits an explicit `None identified` rather than inventing one.
8. **Volatility and failure behavior added** — the saved path is always
   reported with the accepted temp-storage volatility warning and durable-copy
   advice; a failed temp-path or readability check does not fall back to a
   repository or other durable location.
9. **Composition boundary made explicit** — the primitive owns compaction and
   redaction only. PR-review loops, model or reasoning-effort selection,
   implementation and review workflows, and completion policy are reserved
   for declared wrappers.

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
