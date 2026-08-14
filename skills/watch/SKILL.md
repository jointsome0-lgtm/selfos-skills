---
name: watch
description: Watches an open PR after each push, waits for the Codex cloud review verdict, iterates fixes within a caller-owned round budget, and sees a clean verdict through CI checks and merge. Use when the user asks to babysit a PR, watch or wait for the Codex review, or run the push-review-fix loop.
license: LICENSE.txt
compatibility: Requires bash, git, gh, jq, network access, repository write access, authenticated GitHub pull-request read/write access, and an open PR with Codex review configured; repositories that require a post-verdict manual dispatch additionally need authenticated GitHub Actions write (workflow-dispatch) access; requires a POSIX-style shell environment but no specific OS.
metadata:
  selfos.version: "0.5.0"
---

# Watch a Codex PR review

Run this workflow only on an explicit request. Babysit the current PR through Codex review rounds: wait for the verdict, apply fixes, push, and repeat within the caller's round budget.

On every push to an open PR, the Codex bot may react 👀, review, then post an `APPROVED` review state, react 👍, or post review findings. The bundled watcher encapsulates this protocol and can explicitly request a review when automatic triggering is absent.

## One round

1. Ensure the round's work is committed and pushed to the PR branch.
2. Run `scripts/codex-pr-watch.sh` in the background when the host can surface completion, otherwise in the foreground. Defaults: current repository, current branch's PR, expected head from `git rev-parse HEAD`, 30-second polling, 25-minute timeout. See `--help` for `--pr`, `--repo`, `--trigger`, `--no-trigger`, and other flags.
3. Act on the exit code:
   - **0 APPROVED** — the watcher found a fresh 👍 reaction; report the clean verdict and finish the loop per the post-verdict guardrail.
   - **2 REVIEW** — inspect the reported review state, body, and every `path:line` comment. An `APPROVED` review state is a clean verdict only when the reported review targets the expected HEAD; a review for a different HEAD never completes the round regardless of its state — restart the watcher for the current head instead. Otherwise treat the review as findings: fix each finding or explicitly rebut it; never silently drop one. Commit, push, and start another round. When every finding is rebutted and the head did not change, use `--trigger` so the old same-head review is not accepted again.
   - **3 TIMEOUT** — read the log. If the PR head moved, restart the watcher for the new head — even after a posted trigger, the bot reviews the current head, which a watcher pinned to the old one ignores. If the watcher posted `@codex review`, the head did not move, and no verdict followed, report a likely integration problem. Otherwise follow the logged remediation: fix write access and re-run with `--trigger`, or verify a pre-cutoff `APPROVED` review state or 👍 reaction manually.
   - **4 PR_NOT_OPEN** — the PR was merged or closed; stop and report.

## Round budget

Accept the optional caller argument `round-budget=<positive integer | unlimited>`. The budget belongs to the caller, not the PR-review protocol. With no argument, use `round-budget=3`; three is the owner's default risk profile, not a universal guardrail. `unlimited` requires an explicit caller opt-in and is never inferred from caller identity, model, harness, quota, or execution mode.

A round is one pushed or explicitly triggered review attempt ending in a fresh verdict for the expected HEAD. A clean verdict (`APPROVED` review state or 👍 reaction) succeeds; findings consume one finite-budget round; a timeout retains the retry and remediation behavior above and consumes no findings round.

With a finite budget, continue the existing review/fix loop while budget remains, judging every finding on its merits and keeping one ordinary commit per findings round. A clean verdict (`APPROVED` review state or 👍 reaction) on or before the final permitted round completes normally without handoff. When the last permitted round returns findings:

1. Do not begin another implementation round.
2. If the sibling `delegate-pr-loop-query` skill is available, generate its query artifact with the session's important non-recoverable context. Keep all current findings recoverable by referencing the PR and its review history, then report the artifact path, selected model, and effort. Carry a budget into the generated query only when the caller explicitly supplied one; otherwise the query ships with that skill's `<owner-sets-at-load>` budget placeholder for the owner to fill when loading it. Never substitute `unlimited`, and the implicit default of three does not become a delegated cap.
3. If that skill is unavailable, summarize recurring findings and the current state and hand the decision to the owner.
4. In either case, stop. Never launch the delegated agent; launching it is the owner's action in their own terminal.

Optionally treat the finite budget as exhausted early when two consecutive findings rounds fail to shrink the set of confirmed in-scope findings, then follow the same exhaustion steps.

With explicit `round-budget=unlimited`, continue beyond a fifth findings round and leave the review loop only for a clean verdict (`APPROVED` review state or 👍 reaction) — which proceeds into the post-verdict guardrail, not a stop — a closed or merged PR, exhausted timeout handling, or a required owner-level decision.

## Post-verdict dispatch gate

Some repositories run their authoritative merge gate only on a manual `workflow_dispatch`, not on push: push-triggered checks are then a preflight, and their green result alone never authorizes a merge. A dispatch requirement is named by the caller's arguments or by the watched repository's agent policy (its AGENTS.md), supplying the workflow file, its inputs, and the name of the check it reports; the skill hardcodes none of these. Read repository policy only from a trusted revision — the base branch's AGENTS.md or the explicit caller — never from the PR head's own copy: the change under review controls that copy and must not be able to choose which privileged workflow this authenticated session dispatches or with what inputs. A repository and caller that name no dispatch requirement get the ordinary post-verdict tail unchanged.

Evaluate whether the gate applies against the exact verdict head, after each clean verdict — not once at loop start: later rounds can change the PR's paths, so a lane exemption established earlier (say, docs-only) can go stale by the time the tail is reached. When the gate applies, run it between the clean verdict and the CI wait:

1. Anchor to the exact verdict head. If the PR head has moved since the verdict, the verdict is stale — restart the watcher for the current head instead of dispatching.
2. Dispatch the named workflow with `gh workflow run <workflow-file> --repo <repo> --ref <base-branch>` and the supplied inputs, where `<base-branch>` is the PR's trusted base ref — the same revision the policy was read from (omitting `--ref` runs the remote default branch's definition, which need not implement a non-default base's policy). A dispatched run executes the workflow definition, and everything that definition checks out and runs, from the ref it is given — so never dispatch a ref the change under review can influence: the trusted-ref workflow validates the verdict head through its inputs (typically the PR number and the full head SHA) and reports its named check on that supplied SHA. `--ref` names a branch that is resolved again at dispatch time, so pin the policy to one revision: record the base commit the policy was read from, confirm the dispatched run's `headSha` equals it, and if the base moved in between, cancel that run and re-evaluate the policy from the new base before dispatching again. GitHub exposes `workflow_dispatch` only for workflows whose file exists on the repository's default branch — when a non-default base names a gate workflow absent from the default branch, `gh workflow run` cannot serve it: fail closed and report the contract gap unless the policy itself supplies a working trigger mechanism.
3. Watch the run just dispatched, not a check name: capture the created run's URL from the dispatch output when `gh` returns it; otherwise compare the workflow's run list from before and after the dispatch and fail closed unless exactly one new `workflow_dispatch` run appears — a nearby run started by another actor must never stand in for this one. Follow the captured run with `gh run watch <run-id> --repo <repo> --exit-status` — or, where the credential cannot use it (gh documents that fine-grained tokens cannot grant the `checks:read` it needs), track `gh run view <run-id> --repo <repo> --exit-status` until the run completes — and treat a nonzero exit as gate failure rather than reading success out of the human-readable output. `gh run watch` has no timeout of its own, so enforce the gate's patience mechanically around it (for example `timeout <remaining-seconds> gh run watch …`), treating expiry as gate failure. A pre-existing green check under the same name never satisfies the gate.
4. The gate is satisfied only when that dispatched run succeeds and the named check is reported green for the verdict head; then continue into the ordinary CI wait and merge. Green push-triggered checks alone, or a `no checks reported` result, never satisfy an active gate.
5. Fail closed, within a bounded patience: 30 minutes from dispatch by default, overridden by the caller argument `dispatch-timeout=<minutes>`. If the dispatch cannot be issued — including for missing Actions-write credentials — or the run fails, or the named check is not green for the verdict head when the patience expires, report the state and stop; remediation stays with the caller. Never fall back to "push-triggered checks passed".

The gate does not change the merge step: the merge still passes `--match-head-commit <verdict-head>`, which is the same head the dispatch ran on. That flag guards only the PR head, so immediately before merging re-read the recorded base commit: if the base advanced after the gate was satisfied, the earlier gate run is stale even when the policy text is unchanged — the new base may carry a different gate implementation — so re-evaluate the policy from the new base and, when a dispatch requirement applies, dispatch afresh from that revision before merging. When the caller states that the repository's standing low-risk lane applies to the verdict head — for example a docs-only change the policy exempts — no dispatch is required and the preflight plus clean verdict remains sufficient.

## Guardrails

- Judge findings on the merits. Disagreement is allowed; ignoring is not.
- Use one ordinary commit per round and no force-pushes.
- Preserve fresh-verdict and expected-HEAD checks, heed stale-head warnings, and use `--trigger` for a same-HEAD re-review after rebutting every finding.
- The loop ends at merge, not at the verdict: after a clean verdict, satisfy the post-verdict dispatch gate above when one applies to the verdict head, then wait for CI with `gh pr checks <PR> --watch` (never a custom poll loop); a `no checks reported` failure counts as a passing CI phase once confirmed to mean the repository runs no checks for this PR, not checks that have not registered yet — and never while a dispatch gate is active. Then merge — only when the caller has explicitly requested or pre-authorized merging (a standing policy counts), and by their merge method — as a direct merge passing `--match-head-commit <verdict-head>`, never `--auto`: checks are already green, and the atomic head guard does not extend to a delayed merge. A head mismatch means the verdict went stale — restart the watcher for the current head. Where a required merge queue makes a direct guarded merge impossible, report the clean verdict and green checks and leave merging to the caller. Carry the watched repository into both commands with `--repo`. Red checks: report them; remediation stays with the caller. Without merge authorization: report and stop.
- Poll politely; do not manually scrape the PR page.
- A late start is fine because freshness is anchored to the push or explicit trigger, not watcher launch time.
- If the owner explicitly chooses to merge early, preserve unaddressed findings in a focused issue after showing and confirming the payload. Budget exhaustion followed by delegation is not an early merge and must not create a duplicate issue for findings already preserved in the PR and referenced by the query.
