---
name: teach
description: Teaches the user a topic or skill over multiple sessions in a dedicated learning workspace — mission, lessons, learning records, glossary, curated resources. Use when the user asks to be taught something, or wants to start or continue a learning session.
license: LICENSE.txt
compatibility: Requires read/write access to a user-approved learning workspace, network access to research and cite trusted resources, and a browser to view generated HTML. No specific CLI, OS, or authenticated external integration; platform opener access is optional and used only on request.
metadata:
  claude.disable-model-invocation: "true"
  selfos.explicit-only: "true"
---

# Teach

Run this workflow only on an explicit request to start or continue teaching. Read [INSTRUCTIONS.md](INSTRUCTIONS.md) in full and follow its Markdown body plus the bundled format files.

`INSTRUCTIONS.md` is preserved from the earlier distribution and therefore begins with inert legacy YAML metadata. Do not interpret those legacy activation fields as host requirements; this `SKILL.md` is the portable Agent Skills entry point and its metadata controls discovery.
