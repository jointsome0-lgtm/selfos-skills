---
name: delegate-pr-loop-query
description: Creates one ready-to-run GPT-5.6 query that lets a fresh agent continue an open pull request through its remaining Codex review rounds. Use when the current agent must stop operating a PR but the PR still needs review, fixes, and an exact-HEAD clean verdict.
license: LICENSE.txt
compatibility: Requires git, gh, network access, authenticated GitHub pull-request read access, and permission to create one file in the operating system's temporary directory. Repository write access is not used by the delegating run after artifact creation; the generated query may authorize it for the fresh run.
metadata:
  selfos.version: "0.1.0"
---

# Delegate a PR review loop

Use this composite workflow when quota economics require the current orchestrator to stop but the pull request must keep moving on GPT-5.6 quota. Accept an optional focus or constraint and make it prominent in the generated query. This skill creates the query; it never launches or relays the delegated run.

Use the bundled [handoff primitive](references/handoff/SKILL.md) for context selection, durable references, redaction, and suggested-skill discipline. Consult the sibling `compose` skill for current outcome-first structure and model guidance, and name the sibling `watch` skill as the delegated execution workflow. Do not copy either sibling's full instructions into the query.

## 1. Resolve the exact PR state

Complete every read before writing the artifact:

1. Resolve the current Git worktree and its repository root without guessing from the directory name.
2. Resolve the GitHub repository identity from that checkout and the single open pull request for the current branch.
3. Read the local `HEAD`, the PR's `headRefOid`, the PR URL, number, state, title, body, base, current reviews and threads, and checks. Require the PR to be open and the two HEAD SHAs to be identical.
4. Record the exact HTTPS PR URL and full 40-character HEAD SHA. Derive the filename's repository component from the resolved repository name, sanitized to lowercase ASCII letters, digits, and hyphens.

Resolution is read-only. Do not select a different PR because it looks related, accept a shortened SHA, silently use a remote-tracking SHA, or proceed through ambiguous, partial, stale, detached, or mismatched state.

If any required value cannot be established, write no artifact and stop with this structured error:

```text
DELEGATE_PR_LOOP_QUERY_RESOLUTION_FAILED
repository_root: <absolute path | unresolved>
repository: <owner/name | unresolved>
pull_request: <number | unresolved>
pr_url: <HTTPS URL | unresolved>
local_head: <full SHA | unresolved>
pr_head: <full SHA | unresolved>
problem: <missing, ambiguous, closed, or mismatched fact>
next_action: <one concrete way the owner can repair the state>
```

## 2. Compact the continuation context

Read the PR and repository as durable sources, then use the bundled handoff rules to retain only knowledge a fresh agent cannot reliably reconstruct there. Keep:

- the PR's actual feature goal;
- owner-confirmed and in-flight decisions, plan constraints, invariants, and non-goals that must survive;
- rejected approaches and the reason they remain rejected;
- recurring convergence problems or a previously rebutted finding when its conclusion and concrete evidence must be honored if it recurs; and
- uncertainties that materially affect the remaining implementation.

A prior rebuttal is a concise decision plus its evidence, not a copied finding ledger. Reference commits, diffs, review threads, CI runs, specs, ADR-like records, issues, tests, and scripts by path or URL instead of reproducing them. Omit the conversation, routine progress, recoverable review history, command transcripts, and duplicated artifact contents.

Apply the optional focus as a selection constraint, not permission to discard an invariant. Redact credentials, tokens, session identifiers, personal data, private paths, and other sensitive values with typed markers. Review both prose and references after redaction; omit an unsafe reference when redaction would leave it usable only by exposing the value.

## 3. Select model and reasoning effort

Follow the current sibling `compose` guidance when available. Use `gpt-5.6-sol` for frontier, correctness-first review and repair; `gpt-5.6-terra` when the remaining work is well-bounded and balancing capability with cost matters; and `gpt-5.6-luna` only for high-volume, low-risk mechanical continuation. Preserve a caller-specified model when it is compatible with the task and explain the choice in one concise sentence.

Choose exactly one reasoning effort:

- `high` when the remaining work is local, bounded, and well understood;
- `xhigh` when several review rounds exposed recurring or cross-component interactions; or
- `max` only for the hardest unresolved architecture, security, data-integrity, migration, or cross-contract reasoning.

After an exhausted multi-round orchestration budget, default to `xhigh` unless the compacted context clearly supports `high` or `max`. Do not choose `max` merely because several rounds occurred. `ultra` is a separate multi-agent mode and must never appear as the reasoning-effort value.

## 4. Write the single query artifact

Resolve the canonical OS temporary directory through the host runtime. Create one unpredictable owner-only temporary directory beneath it and exactly one Markdown file inside, named `<repo>-pr-<number>-loop-query.md`. Use exclusive creation with owner-only file permissions where supported. Write no repository file and no second handoff, sidecar, log, or metadata artifact.

The file has exactly these top-level sections and follows the lean sibling `compose` structure:

```markdown
# Run configuration

Model: <gpt-5.6-sol | gpt-5.6-terra | gpt-5.6-luna>
Reasoning effort: <high | xhigh | max>
Reason: <one concise sentence>

# Query

## Goal
Complete <exact PR URL> correctly and maintainably from exact HEAD `<full SHA>`, preserving the original feature goal and repository contracts, and continue until the exact final HEAD has a fresh clean Codex verdict.

## Context
- Repository and PR: <owner/name, PR title, URL, base, and exact starting HEAD>
- Original goal: <the actual feature outcome>
- Delegation focus: <optional focus, omitted when absent>
- Non-recoverable handoff: <decisions, invariants, rejected approaches, recurring rebuttals with evidence, and material uncertainties only>
- Durable references: <concise paths or URLs; do not reproduce their contents>

## Constraints
- Inspect the exact starting HEAD and current review state before changing anything; if the PR head moved, reconcile that state explicitly rather than assuming the query's SHA is current.
- Verify every finding on its merits. Fix valid findings coherently, add regression coverage where appropriate, and rebut false positives with concrete repository evidence instead of complying merely to silence review.
- A clean verdict is the completion signal, not the optimization objective. Do not weaken intended behavior, schemas, validators, error handling, contracts, or meaningful tests merely to silence review.
- `round-budget=unlimited`. This caller-provided budget overrides `watch`'s ordinary finite-round handoff guardrail for this run; never infer a budget from the caller's identity, model, quota, harness, or execution mode.
- You may read repository and PR state, edit in-scope files, add or update tests, run non-destructive validation, commit and push to the current PR branch, and trigger and monitor Codex review rounds.
- The environment caps one command at about 10 minutes. Run the `watch` watcher with `--timeout 540` and re-run it as needed; starting it late is safe because freshness is anchored to the push or explicit trigger, not watcher launch time.

## Success criteria
- Relevant repository validation and regression tests pass, with evidence reported.
- Every finding is fixed or rebutted with concrete repository evidence.
- In-scope fixes are committed and pushed without force-pushes, using one ordinary commit per review round.
- `watch` continues until the exact final HEAD receives a fresh clean verdict; report that SHA and approval evidence.

## Stop rules
- Stop for an owner-level product or specification conflict, an unauthorized destructive action, or genuinely incompatible requirements.
- If repository, PR, HEAD, or review freshness cannot be established, stop with a structured failure instead of guessing.
- Otherwise continue the explicitly unbounded review loop; do not introduce an artificial round cap.

## Suggested skills

- `watch`
```

Replace every placeholder with resolved, redacted content. Keep the quality-preservation sentence exactly once in the generated query. Do not add an Output section that asks for a second artifact; the delegated run's final report is enough.

Confirm that the final path is inside the canonical temporary directory, the filename matches the resolved repository and PR number, the file is readable, and the query records the exact PR URL and HEAD SHA. On a failed check, remove the attempted file when safe and report a structured artifact error instead of falling back to the repository.

## 5. End the delegating session

After the file passes its checks, print only the saved path, selected model, selected effort, and a short warning that OS temporary storage is volatile. From that point, make no PR or repository mutation, do not trigger another review, do not invoke `watch`, and never launch the delegated query. End the current workflow. The owner starts it detached in their own terminal; later verification belongs in a fresh short session.

Invented fixture evidence and expected selection behavior are in [EXAMPLES.md](EXAMPLES.md).
