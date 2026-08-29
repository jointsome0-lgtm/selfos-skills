# Provenance — skills/unslop

## skills/unslop/SKILL.md

| Field | Value |
| --- | --- |
| Upstream repository | `cursor/plugins` |
| Upstream path | `pstack/skills/unslop/SKILL.md` |
| Blob | `2a93c06bbe54fde89a36c88e63ef07477da323d4` |
| Imported | 2026-08-29 |
| License | MIT (notice below; `pstack/LICENSE`) |
| Status | **adapted** |

Named deviations — the process, the "Adding soul" section, and all 31
numbered patterns are verbatim upstream text:

1. **Catalog placement and portable metadata added** — the upstream skill is
   placed at canonical `skills/unslop/`; its description is rewritten as a
   "Use when" trigger, and local license, compatibility, and
   `metadata.selfos.version` fields are added. The description itself
   follows the skill's own rules (no em dashes).
2. **"Must always apply" made portable** — upstream's frontmatter
   description ends with "Must always apply.", an always-on directive that
   only its host plugin honors. The catalog has no host-neutral always-on
   flag, so the directive becomes a body paragraph: apply to every piece of
   prose written for a reader and to any text the owner points at.
   Invocation is automatic or explicit via the description trigger.
3. **Scope boundary added** — new prose with no upstream counterpart: code,
   quoted material, and other people's words stay untouched unless the owner
   asks to edit them.

## Upstream license notice

```
MIT License

Copyright (c) 2026 Lauren Tan

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
