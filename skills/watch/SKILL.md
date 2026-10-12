---
name: watch
description: Use when completing an assigned open PR with Codex review and permission to merge, or when asked to watch its review. Require a fresh verdict for the final commit, resolve blocking findings, and verify CI before merging.
license: LICENSE.txt
compatibility: Requires Python 3.8 or later, git, gh with authenticated GitHub API access, and a PR on which the Codex bot keeps its review summary comment. Writes need the permissions for the authorized push, review request, merge, or workflow dispatch.
metadata:
  selfos.version: "3.0.0"
---

# Watch a Codex PR review

Use this for the PR covered by the current task. Invocation grants no permission to edit, post comments, dispatch workflows, or merge; existing explicit or standing authorization remains sufficient.

## Review loop

Watch the current pushed commit, and watch again after every push, including CI fixes. Take the full SHA from `git rev-parse HEAD` in the pushed checkout. Resolve the watcher's path relative to this skill:

```sh
python3 scripts/codex_pr_watch.py --repo OWNER/REPO --pr NUMBER --sha FULL_SHA
```

Run it in the background when the host reports completion. It only reads. With `--trigger` it posts `@codex review` once; use that only when review-request comments are authorized and no review starts by itself. The first output line names the verdict:

- **0 APPROVED:** the bot's summary reports a completed review of this commit, and the bot's 👍 came with it, with no review.
- **2 FINDINGS:** the bot reviewed this commit. Assess the printed review body and every inline comment under the merge threshold.
- **3 TIMEOUT** or **1 ERROR:** no verdict. Follow [recovery](references/recovery.md).
- **4 PR_NOT_OPEN:** report the state and stop.

Fix confirmed blockers within scope, or rebut false positives with evidence. Use one ordinary commit per repair round and no force-pushes. Every changed head needs a new verdict; an earlier one never authorizes merging a later commit. An unchanged head with an accepted verdict needs no further review.

Honor `round-budget`, defaulting to three verdicts with remaining blockers; only the caller can choose `unlimited`. Stop before another repair when it is exhausted. [Recovery](references/recovery.md) defines counting and handoff.

## Merge threshold

Apply the caller's threshold and trusted repository requirements, including required approvals. Otherwise confirmed P0/P1 findings block. Judge consequences rather than the badge: a lower or unlabelled finding with a demonstrated functional failure blocks too.

A verdict for the exact head with no remaining blockers is accepted, even with nonblocking findings. End the repair loop and continue through the gates below. Report what remains and why it is nonblocking; do not call that a clean review.

## Post-verdict dispatch policy

After each accepted verdict, record the base ref and commit. Read the caller's requirements and the root and every applicable nested AGENTS.md from that trusted base, for the current changed paths. PR-head policy cannot choose a privileged workflow or its inputs.

Satisfy every required contract; one gate never waives another. Use an exemption only when the caller confirms it and trusted policy permits it. Only when dispatch is required, follow [the dispatch procedure](references/dispatch-gate.md) before the CI wait.

## CI and merge

Wait for the verdict head's checks with `gh pr checks NUMBER --repo OWNER/REPO --watch`. Accept a `no checks reported` result only after confirming that the PR has no checks; it never satisfies a dispatch gate. Fix the cause of a red check within scope, and correct a faulty test or workflow rather than bending working code to it.

A pushed code, test, or workflow fix restarts review and every applicable gate. A CI rerun on an unchanged head can reuse the accepted verdict.

Immediately before merging, recheck that the PR is open, its head equals the verdict SHA, and its base ref and commit are unchanged. A moved head restarts review. A changed base requires fresh policy evaluation and all applicable gates again, even when the policy text is unchanged.

Merge only with explicit or standing caller authorization, no blockers, required approvals, and successful CI and dispatch gates. Use the authorized method and message, an explicit `--repo`, and `--match-head-commit FULL_VERDICT_SHA`. Merge directly, never with `--auto`. If a required queue prevents this, or merging is not authorized, report readiness and stop.

Create follow-up issues only when requested.
