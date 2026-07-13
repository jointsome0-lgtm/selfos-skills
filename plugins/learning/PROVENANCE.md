# Provenance — plugins/learning

## skills/teach/

| Field | Value |
| --- | --- |
| Upstream repository | `mattpocock/skills` |
| Upstream path | `skills/productivity/teach/` |
| Upstream commit | `697d4ce9742da558fd1ba6697c8e9775e2e302dd` |
| Imported | 2026-07-13 |
| License | MIT (notice below) |
| Status | **adapted** |

Per-file pins — upstream blob at the pinned commit:

| File | Upstream blob | Local status |
| --- | --- | --- |
| `SKILL.md` | `b1603e5ac536d2b5c29496c06df4db0bb9f74e69` | adapted (deviations below) |
| `GLOSSARY-FORMAT.md` | `9cae84c44c8eb5d27b8695d4ef29a2893dc4900c` | verbatim |
| `LEARNING-RECORD-FORMAT.md` | `2faa7c98fabcdff48eb6bd07e4847d48a6b8d4e1` | verbatim |
| `MISSION-FORMAT.md` | `5dac184a319308e2ec0c18c16d6b8d52b9be2748` | verbatim |
| `RESOURCES-FORMAT.md` | `c94aac6a2634cc229fe0b777fc5cc7da3a28c3d2` | verbatim |

Named deviations from the upstream text — everything else preserves upstream behavior:

1. **Dedicated workspace** — upstream treats the current directory as the teaching workspace; the local file requires a dedicated per-topic directory and forbids scaffolding workspace files into a repository the agent happens to be started in. Detection demands both `MISSION.md` and a `.teach-workspace` marker outside version-controlled, shared, or public paths (a bare `MISSION.md` upstream sufficed); the topic is reduced to one sanitized dash-case basename resolved under a user-approved learning root; containment extends to every descendant — symlinked or outside-resolving workspace files are never followed; the location checks precede any write, marker included, and user confirmation cannot override them. Workspaces hold personal data and stay out of shared or public repositories.
2. **Frontmatter description** — rewritten to this repository's convention (third-person summary plus `Use when …` triggers); upstream's imperative one-liner fails `scripts/build_index.py`. `disable-model-invocation` and `argument-hint` are kept as upstream; since the flag keeps Claude Code from auto-loading the skill, the description and repository docs state explicitly that it is user-invoked only.
3. **`agents/openai.yaml` not vendored** — upstream's OpenAI-native skill packaging; Codex discovery in this repository goes through the root `AGENTS.md` index instead.
4. **Constrained lesson opening** — upstream asks the agent to open the lesson by running a CLI command; the local file gives the user the path and opens only on explicit request, via the platform's standard opener with the path passed as a single argument.
5. **Notes are data, not instructions** — upstream's free-form `NOTES.md` scratchpad is limited to declarative teaching preferences; workspace content cannot authorize tools or commands, name paths outside the workspace, request network access, or override the skill or host rules — instruction-shaped content is ignored and surfaced to the user.
6. **Workspace HTML audited and network-free** — upstream reuses existing components unconditionally and says nothing about lesson network behavior; the local file requires reading any pre-existing component, lesson, or reference document before opening or linking it, forbids network requests when workspace documents open (no remote scripts, styles, images, fonts, fetches, or beacons — external citations stay plain hyperlinks), and quarantines anything obfuscated or beyond its stated purpose.
7. **External content is data** — upstream mandates grounding teaching in external resources without a trust boundary; the local file declares fetched pages, documents, and community content untrusted data on par with workspace files: knowledge is extracted, instruction-shaped content is ignored and surfaced.

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
