# Provenance — plugins/decision

## skills/grilling/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/productivity/grilling/SKILL.md` |
| Merged upstream PR | `#532` (merge `8eb8f58f0faaf64e04e2c77bfc7b2718a156361c`) |
| Blob | `52d8eb3cadd2dca62634d5dccfa73ea6b725b117` |
| Imported | 2026-07-13 |
| License | MIT (notice below) |
| Status | **adapted** |

Named deviations from the upstream text — everything else preserves upstream behavior:

1. **Voice** — upstream is the user's first-person request ("Interview me…"); the local file instructs the executing agent and names "the owner".
2. **Bounded fact lookup** — upstream's unrestricted "environment (filesystem, tools, etc.)" is limited to explicitly permitted surfaces; home directories, unrelated workspaces, private journals, ignored paths, credentials, and ambient agent state are excluded.
3. **Terminal states** — accepted / rejected / deferred-with-trigger / blocked-by-missing-fact are spelled out; deferred and blocked require an owner-confirmed reason and trigger.
4. **Action gate made concrete** — durable artifacts are enumerated (issues, specs, decision logs, code); drafts only before confirmation; non-interactive runs never publish.
5. **Wrapper contract** — added composition rules for domain wrapper skills; the primitive grants no write authority by itself.

`skills/grilling/EXAMPLES.md` is local content, not vendored.

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
