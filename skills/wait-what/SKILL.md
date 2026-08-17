---
name: wait-what
description: Use when the owner explicitly says they lost the thread, asks "wait, what?", or asks for the last message explained again simply — re-pitches the previous assistant message in Simplified Technical English using the repository's established domain terms.
license: LICENSE.txt
compatibility: No specific CLI, OS, network access, repository write access, or external integration is required.
disable-model-invocation: true
metadata:
  selfos.version: "0.1.1"
  selfos.explicit-only: "true"
---

# Re-pitch the last message

Run this skill only on an explicit owner request; never activate it from a topical match.

The owner did not understand where the work has got to. Re-pitch the previous assistant message: give a little context on where the work stands, then restate what that message was saying.

Write the re-pitch in ASD-STE100 Simplified Technical English.

For terminology, use the ubiquitous language from the repository's SDD or domain-model document when one exists; otherwise use plain, jargon-free wording. Introduce any term the owner has not seen in this conversation before relying on it.

This skill only restates; it does not advance the work, change any file, or make any decision.
