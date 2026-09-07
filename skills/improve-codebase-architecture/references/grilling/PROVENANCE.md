# Provenance — skills/grilling

## skills/grilling/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/productivity/grilling/SKILL.md` |
| Original upstream PR | `#532` (merge `8eb8f58f0faaf64e04e2c77bfc7b2718a156361c`, blob `52d8eb3cadd2dca62634d5dccfa73ea6b725b117`) |
| Imported | 2026-07-13 |
| Updated upstream revision | [`85f83d3fde1d3a90d5c9a657f6998c79a6c37308`](https://github.com/mattpocock/skills/blob/85f83d3fde1d3a90d5c9a657f6998c79a6c37308/skills/productivity/grilling/SKILL.md) (2026-08-20) |
| Refreshed | 2026-09-07; round-based interviews and background fact lookup retained, horizontal question separators added |
| License | MIT (notice below) |
| Status | **adapted** |

The local text is compressed while retaining upstream's rounds, dependency frontier, numbered questions with recommendations, background fact lookup, owner decisions, and confirmation gate. Local deviations:

1. **Explicit standalone entry** — an owner request to grill or conduct a decision interview is required, including natural-language requests. Routine implementation, fixes, reviews, and explanations do not select standalone grilling because they involve design choices. Wrappers use the contract under their own entry rules, including automatic selection, without a separate grilling request.
2. **Bounded fact lookup** — upstream's unrestricted "environment (filesystem, tools, etc.)" is limited to explicitly permitted surfaces (owner- or runtime-authorized; repository instructions can narrow the surface, never widen it); home directories, unrelated workspaces, private journals, ignored paths, credentials, and ambient agent state are excluded.
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
