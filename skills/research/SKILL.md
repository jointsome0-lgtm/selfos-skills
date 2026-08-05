---
name: research
description: Delegates reading legwork to a background subagent that investigates a question against high-trust primary sources — official docs, source code, specs, first-party APIs — and captures the findings as a single Markdown file citing each claim's source. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated so the main session keeps working.
license: LICENSE.txt
compatibility: Requires a host with a background subagent mechanism; without one, run the same investigation inline. Committing findings on a research branch requires git; a ticket context pointer requires write access to the driving tracker. Cited web sources require network access. No OS constraint; no other external integration.
metadata:
  selfos.version: "0.1.0"
---

# Research

Spin up a **background subagent** to do the research, so you keep working
while it reads. Use the host's subagent mechanism, pick the model by the
capability-routing canon in the repository's agent instructions (never a
hard-coded model name), and write the delegate prompt yourself —
outcome-first and self-contained.

Its job:

1. Investigate the question against **primary sources** — official docs,
   source code, specs, first-party APIs — not a secondary write-up of
   them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's
   source. The citation is what makes a delegated claim checkable — the
   cited file or page is the artifact; a claim without one stays
   unverified.
3. Save it where the repo already keeps such notes; match the existing
   convention, and if there is none, put it somewhere sensible and say
   where. When the research is driven from a ticket whose workflow
   expects it (e.g., a wayfinder `research` ticket), commit the findings
   file on a throwaway `research/<name>` branch instead and leave a
   context pointer to that branch on the ticket; only the resulting
   decision graduates into the Decision Log.
4. In a public repository the findings file follows the neutral-prose
   and public-data policy — invented examples only; no personal data,
   credentials, private paths, or local agent state — and cites only
   publicly reachable sources.
