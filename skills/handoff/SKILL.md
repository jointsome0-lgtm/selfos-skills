---
name: handoff
description: Creates one compact, privacy-safe Markdown handoff in the operating system's temporary directory so a fresh agent can resume from durable artifacts and only the context it cannot recover. Use when work must continue in a fresh session, either directly or as a primitive invoked by a composite workflow.
license: LICENSE.txt
compatibility: Requires permission to create one file in the operating system's temporary directory. No specific CLI, OS, network access, repository write access, or external integration is required.
metadata:
  selfos.version: "0.1.0"
---

# Create a compact handoff

Create one compact Markdown document that lets a fresh agent resume the work. The owner may supply an optional description of the next session's focus; when present, make that focus the document's organizing priority and omit unrelated detail.

This skill owns context compaction and redaction only. It remains usable directly and may be vendored and invoked by a declared composite skill. A wrapper may add its own domain policy, but this primitive does not choose or prescribe implementation, review, PR-loop, model, reasoning-effort, or completion policy.

## Select the context

Capture:

- the current goal;
- meaningful progress that changes what remains;
- unresolved blockers;
- non-obvious decisions and constraints the next agent must preserve; and
- the optional next-session focus, if supplied.

Include only context a fresh agent cannot reliably recover from durable artifacts. Do not include a transcript, chain-of-thought, copied GitHub finding ledger, or routine investigative detail.

Reference durable artifacts by path or URL instead of copying their contents. Prefer precise references to relevant specs, plans, ADRs, issues, commits, diffs, and PR threads. Add a short description only when the reference alone would be ambiguous.

## Redact before writing

Remove credentials, API keys, tokens, passwords, session identifiers, cookies, private keys, personal data, and any other sensitive values from both prose and artifact references. Replace each removed value with a typed marker such as `[REDACTED: token]` or `[REDACTED: personal data]`; do not preserve a prefix, suffix, or reversible form of the value.

Review the complete document for sensitive values after drafting it. If safe redaction would make a reference unusable, omit that reference and describe the missing artifact generically.

## Document shape

Use this compact structure, omitting an empty optional section rather than padding it:

```markdown
# Handoff

## Next-session focus
<the supplied focus, reflected in what the document emphasizes>

## Current goal
<the outcome being pursued>

## Meaningful progress
<only progress that affects continuation>

## Unresolved blockers
<blockers, or "None known">

## Decisions and constraints
<non-obvious facts the next agent must preserve>

## Durable references
- <path or URL> — <why it matters, only when useful>

## Suggested skills
- `<skill name>` — <why it would help the next session>
```

The `Suggested skills` section is always present. Recommend only skills that plausibly help with the stated focus and remaining work; write `None identified` when no useful skill is known.

## Write exactly one temporary file

Resolve the operating system's canonical temporary directory through the host runtime's temp-directory facility. Create exactly one new file there with an unpredictable `handoff-<timestamp>-<random>.md` name, using exclusive creation and owner-only permissions when the host supports them. Do not write to the current repository or workspace, and do not clean, reset, or otherwise alter its pre-existing state.

Before reporting success, confirm that the resolved file path is inside the canonical temporary directory and that the document is readable. If either check fails, remove the attempted output when safe and report failure rather than writing elsewhere.

Always report the saved path. Also state that OS temporary storage is volatile and may disappear after reboot or cleanup, so the owner should copy the file to a durable approved location when the gap before the next session may be long.
