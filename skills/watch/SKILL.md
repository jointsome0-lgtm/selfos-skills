---
name: watch
description: Watches an open PR after each push, waits for the Codex cloud review verdict, and iterates fixes within a caller-owned round budget. Use when the user asks to babysit a PR, watch or wait for the Codex review, or run the push-review-fix loop.
license: LICENSE.txt
compatibility: Requires bash, git, gh, jq, network access, repository write access, authenticated GitHub pull-request read/write access, and an open PR with Codex review configured; requires a POSIX-style shell environment but no specific OS.
metadata:
  selfos.version: "0.2.0"
---

# Watch a Codex PR review

Run this workflow only on an explicit request. Babysit the current PR through Codex review rounds: wait for the verdict, apply fixes, push, and repeat within the caller's round budget.

On every push to an open PR, the Codex bot may react 👀, review, then post an `APPROVED` review state, react 👍, or post review findings. The bundled watcher encapsulates this protocol and can explicitly request a review when automatic triggering is absent.

## One round

1. Ensure the round's work is committed and pushed to the PR branch.
2. Run `scripts/codex-pr-watch.sh` in the background when the host can surface completion, otherwise in the foreground. Defaults: current repository, current branch's PR, expected head from `git rev-parse HEAD`, 30-second polling, 25-minute timeout. See `--help` for `--pr`, `--repo`, `--trigger`, `--no-trigger`, and other flags.
3. Act on the exit code:
   - **0 APPROVED** — the watcher found a fresh 👍 reaction; report the clean verdict and stop.
   - **2 REVIEW** — inspect the reported review state, body, and every `path:line` comment. An `APPROVED` review state is a clean verdict; report it and stop. Otherwise treat the review as findings: fix each finding or explicitly rebut it; never silently drop one. Commit, push, and start another round. When every finding is rebutted and the head did not change, use `--trigger` so the old same-head review is not accepted again.
   - **3 TIMEOUT** — read the log. If the PR head moved, restart the watcher for the new head — even after a posted trigger, the bot reviews the current head, which a watcher pinned to the old one ignores. If the watcher posted `@codex review`, the head did not move, and no verdict followed, report a likely integration problem. Otherwise follow the logged remediation: fix write access and re-run with `--trigger`, or verify a pre-cutoff `APPROVED` review state or 👍 reaction manually.
   - **4 PR_NOT_OPEN** — the PR was merged or closed; stop and report.

## Round budget

Accept the optional caller argument `round-budget=<positive integer | unlimited>`. The budget belongs to the caller, not the PR-review protocol. With no argument, use `round-budget=5`; five is the owner's unchanged default risk profile, not a universal guardrail. `unlimited` requires an explicit caller opt-in and is never inferred from caller identity, model, harness, quota, or execution mode.

A round is one pushed or explicitly triggered review attempt ending in a fresh verdict for the expected HEAD. A clean verdict (`APPROVED` review state or 👍 reaction) succeeds; findings consume one finite-budget round; a timeout retains the retry and remediation behavior above and consumes no findings round.

With a finite budget, continue the existing review/fix loop while budget remains, judging every finding on its merits and keeping one ordinary commit per findings round. A clean verdict (`APPROVED` review state or 👍 reaction) on or before the final permitted round completes normally without handoff. When the last permitted round returns findings:

1. Do not begin another implementation round.
2. If the sibling `delegate-pr-loop-query` skill is available, generate its query artifact with the session's important non-recoverable context. Keep all current findings recoverable by referencing the PR and its review history, then report the artifact path, selected model, and effort. Carry a finite cap into the generated query only when the caller explicitly supplied one; the implicit default of five does not become a delegated cap.
3. If that skill is unavailable, summarize recurring findings and the current state and hand the decision to the owner.
4. In either case, stop. Never launch the delegated agent; launching it is the owner's action in their own terminal.

Optionally treat the finite budget as exhausted early when two consecutive findings rounds fail to shrink the set of confirmed in-scope findings, then follow the same exhaustion steps.

With explicit `round-budget=unlimited`, continue beyond a fifth findings round and stop only for a clean verdict (`APPROVED` review state or 👍 reaction), a closed or merged PR, exhausted timeout handling, or a required owner-level decision.

## Guardrails

- Judge findings on the merits. Disagreement is allowed; ignoring is not.
- Use one ordinary commit per round and no force-pushes.
- Preserve fresh-verdict and expected-HEAD checks, heed stale-head warnings, and use `--trigger` for a same-HEAD re-review after rebutting every finding.
- Poll politely; do not manually scrape the PR page.
- A late start is fine because freshness is anchored to the push or explicit trigger, not watcher launch time.
- If the owner explicitly chooses to merge early, preserve unaddressed findings in a focused issue after showing and confirming the payload. Budget exhaustion followed by delegation is not an early merge and must not create a duplicate issue for findings already preserved in the PR and referenced by the query.
