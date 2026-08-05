---
name: research
description: Delegates reading legwork to a background subagent that investigates a question against high-trust primary sources — official docs, source code, specs, first-party APIs — and captures the findings as a single Markdown file citing each claim's source. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated so the main session keeps working.
license: LICENSE.txt
compatibility: Requires a background subagent mechanism (without one, run the investigation inline), network access for web sources, and write access to the repository checkout to save findings — in a read-only checkout, write to the host's temporary directory and say where. Ticket-driven capture also needs git worktree support, tracker write access, and push access to the remote; without a writable remote the branch stays local and the pointer says so. No OS constraint; no other external integration.
metadata:
  selfos.version: "0.1.0"
---

# Research

Spin up a **background subagent** to do the research, so you keep working
while it reads. Use the host's subagent mechanism, pick the model by the
capability-routing canon in the repository's agent instructions (never a
hard-coded model name), and write the delegate prompt yourself —
outcome-first and self-contained. On a host with no background subagent
mechanism, run the same investigation inline in the current session
instead — never skip the research because delegation is unavailable.

The research job:

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
   file on a throwaway `research/<name>` branch instead — created in a
   worktree at `<repo>/.worktrees/<name>`, never in the primary
   checkout, after making sure `.worktrees/` is ignored (repository
   `.gitignore`, `.git/info/exclude`, or a global git ignore file) so
   the worktree never shows up as an untracked path — and push the branch, then leave a context pointer to it on the
   ticket; when no writable remote exists, the branch stays local and
   the pointer says so. Only the resulting decision graduates into the
   Decision Log.
4. In a public repository the findings file follows the neutral-prose
   and public-data policy — invented examples only; no personal data,
   credentials, private paths, or local agent state — and cites only
   publicly reachable sources.
