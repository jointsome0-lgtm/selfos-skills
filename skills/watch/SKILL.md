---
name: watch
description: Use when an open PR needs babysitting through the Codex review loop — waits for each verdict, fixes blocking findings within the caller's round budget, and proceeds through CI and authorized merge when none remain.
license: LICENSE.txt
compatibility: Requires bash, git, gh, jq, network access, repository write access, authenticated GitHub pull-request read/write access, and an open PR with Codex review configured; repositories that require a post-verdict manual dispatch additionally need authenticated GitHub Actions write (workflow-dispatch) access; requires a POSIX-style shell environment but no specific OS.
metadata:
  selfos.version: "2.1.0"
---

# Watch a Codex PR review

Run only on an explicit request. Wait for Codex review, resolve blocking findings within the caller's round budget, then satisfy CI and any authorized merge.

## Review loop

1. Commit and push the round's work. Run `scripts/codex-pr-watch.sh`, in the background when the host can surface completion. Pass the actual full expected commit SHA with `--sha`, using `git rev-parse HEAD` in the pushed checkout; use `--repo` and `--pr` when the checkout does not identify the target. The script retries a failed head lookup once and waits for GitHub to report the expected head before requesting or accepting review. See `--help` for defaults and other flags.
2. Act on the exit code:
   - **0 APPROVED:** a fresh bot 👍 was accepted. Continue to the post-verdict gate and merge conditions below.
   - **2 FINDINGS:** read the review state, body, and every inline comment. Assess every finding under the merge threshold below, including comments on an `APPROVED` review. Fix blocking findings and rebut false positives with evidence. If no blockers remain, accept the verdict and continue to the post-verdict gate and merge conditions.
   - **3 TIMEOUT:** follow the logged remediation for a moved head, missing trigger, or access failure. A pre-cutoff verdict needs manual freshness verification. If a trigger was posted, the head stayed fixed, and no verdict followed, report the integration problem and stop. An 👀 reaction alone does not justify more triggers.
   - **4 PR_NOT_OPEN:** report that the PR was closed or merged and stop.
   - **1 ERROR:** resolve the reported usage or lookup failure before retrying.
3. For fixes, use one ordinary commit per findings round and no force-pushes. Push and repeat while budget remains. With no blockers and an unchanged SHA, proceed without requesting another review.

The watcher ignores reviews for other SHAs. It anchors freshness to the push or explicit trigger, so a late start is valid. After a head change, restart for the new head; an earlier verdict never authorizes merging the new one. Poll through the watcher, never by scraping the PR page.

Use a local or external review after an integration failure only when the caller selects that fallback. Record its full reviewed SHA and apply the same round budget and merge gates.

## Merge threshold

By default, confirmed P0/P1 findings block merge. P2 and lower do not unless demonstrated impact warrants P0/P1 severity, such as a critical functional failure or severe performance regression. Judge consequences rather than trusting the badge; assess unlabelled findings the same way. Honor stricter caller or trusted repository requirements, including required approvals.

A fresh verdict for the exact HEAD with no remaining blockers is an accepted verdict, even with nonblocking findings. End the repair loop and proceed through the gates below, including on the last budgeted round. Briefly report any remaining findings and why they are nonblocking; do not claim a clean review when findings remain. Do not start another fix or review round, request renewed merge permission, or require a follow-up issue solely for nonblocking findings.

For contract-test PRs blocked by an unimplemented API, rebut speculative hardening requests together and link the implementing PR when one exists. Explain which assertions define the agreed contract and which hardening needs executable behavior. Fold cheap in-scope corrections into an already needed repair round. This does not waive required CI or confirmed blockers, or start a new round solely for nonblocking findings.

## Round budget and handoff

Accept `round-budget=<positive integer | unlimited>`, defaulting to `3`. Only an explicit caller choice enables `unlimited`; never infer it from the model, harness, identity, or quota.

Each fresh verdict with remaining blockers for the expected SHA consumes one finite-budget round. Timeouts consume none. An accepted verdict, including on the final permitted round, proceeds to CI and any authorized merge. With `unlimited`, continue until an accepted verdict, a closed or merged PR, exhausted timeout remediation, or an owner-level decision.

If blockers remain after the last permitted round, begin no further implementation round. Optionally exhaust a finite budget early when two consecutive findings rounds fail to shrink the confirmed in-scope blockers.

The current agent owns the PR through completion within these gates and the round budget. Wait for CI and review through the watcher and check commands; waiting alone is no reason to delegate the loop. Budget exhaustion means reporting the blocker, not transferring it to a new agent to restart the budget.

Hand off only when the owner requests it or the current session cannot continue, for example because context or execution capacity is exhausted. Use the installed `handoff` skill when available; otherwise provide a compact continuation in the final response. Include the verified PR URL and full current HEAD SHA, goal, constraints, remaining work, and consumed and remaining review budget. Identify any local changes outside that HEAD without altering them; mark unavailable state as unverified. Keep sensitive data out and link existing review threads rather than copying a findings ledger. Handoff does not launch another agent or grant new rounds, permissions, or a model change.

## Post-verdict dispatch policy

After each accepted verdict, evaluate dispatch requirements for its exact head and changed paths. Use the caller's instructions or trusted base-branch policy: record the PR's base ref and commit, then read the root AGENTS.md and every nested AGENTS.md whose directory contains a changed path, all from that revision. Never use PR-head policy to choose a privileged workflow or its inputs. Resolve each path's policy under normal scope precedence and satisfy every distinct dispatch-and-check contract; one gate never waives another. The caller or policy supplies the workflow, inputs, and reported check name.

Without a dispatch requirement, continue to CI and merge. A caller-confirmed standing low-risk lane may exempt the current verdict head when the trusted policy permits it. Reevaluate after every accepted verdict; earlier path-based exemptions can become stale.

Only when dispatch is required, read [the dispatch procedure](references/dispatch-gate.md) and complete it before the CI wait. Both the dispatched run and its named check on the verdict head must succeed; green push checks alone never satisfy this gate.

Immediately before merging, recheck the PR head, base ref, and base commit. A moved head needs a fresh review. If the base advanced or the PR was retargeted, every earlier policy conclusion is stale, including "no dispatch applies", even if the policy text is unchanged: the workflow implementation may have changed. Reevaluate against the current base and changed paths, and satisfy every applicable gate afresh under that policy before merging.

## CI and merge

After the accepted verdict and all applicable dispatch gates, wait with `gh pr checks <PR> --repo <repo> --watch`. A `no checks reported` failure passes this phase only after confirming that this PR has no checks, rather than checks that have not registered; it never satisfies an active dispatch gate. For red checks, inspect the failing logs and reproduce the failure where practical. Compare the failure with the intended behavior to distinguish a code defect from an incorrect test, broken CI configuration, or infrastructure failure. Fix the cause within the authorized scope; correct faulty tests or CI rather than distorting working code to satisfy them. Preserve useful checks and intended behavior. Retry transient infrastructure failures within bounded patience; report a blocker when recovery needs unavailable access or an owner decision.

After a code, test, or workflow fix, validate it, commit and push, then obtain a fresh accepted verdict for the new exact HEAD before repeating applicable gates and CI. A rerun without a head change can reuse the accepted verdict. CI failures do not consume review rounds; any new review with remaining blockers does.

Merge only with explicit or standing caller authorization, using their merge method, any prepared message file, and `--match-head-commit <verdict-head>`. Use a direct merge, never `--auto`: the head guard does not protect a delayed merge. Carry `--repo` into the merge command. Recheck the base policy as required above; if the PR head moved, restart review for that head. If a required merge queue prevents direct guarded merge, or merging is not authorized, report the accepted verdict and green checks and stop.

Create follow-up issues only when requested; remaining findings are already recorded in the PR.
