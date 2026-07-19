---
name: watch
description: Watches an open PR after each push, waits for the Codex cloud review verdict, and iterates fixes in-session until approval. Use when the user asks to babysit a PR, watch or wait for the Codex review, or run the push-review-fix loop.
license: LICENSE.txt
compatibility: Requires bash, git, gh, jq, network access, and an open GitHub pull request with Codex review configured.
metadata:
  selfos.explicit-only: "true"
---

# Watch a Codex PR review

Run this workflow only on an explicit request. Babysit the current PR through Codex review rounds: wait for the verdict, apply fixes, push, and repeat in one session.

On every push to an open PR, the Codex bot may react 👀, review, then either react 👍 or post review findings. The bundled watcher encapsulates this protocol and can explicitly request a review when automatic triggering is absent.

## One round

1. Ensure the round's work is committed and pushed to the PR branch.
2. Run `scripts/codex-pr-watch.sh` in the background when the host can surface completion, otherwise in the foreground. Defaults: current repository, current branch's PR, expected head from `git rev-parse HEAD`, 30-second polling, 25-minute timeout. See `--help` for `--pr`, `--repo`, `--trigger`, `--no-trigger`, and other flags.
3. Act on the exit code:
   - **0 APPROVED** — report the clean verdict and stop.
   - **2 FINDINGS** — read the review body and every `path:line` comment. Fix each finding or explicitly rebut it; never silently drop one. Commit, push, and start another round. When every finding is rebutted and the head did not change, use `--trigger` so the old same-head review is not accepted again.
   - **3 TIMEOUT** — read the log. If the PR head moved, restart the watcher for the new head — even after a posted trigger, the bot reviews the current head, which a watcher pinned to the old one ignores. If the watcher posted `@codex review`, the head did not move, and no verdict followed, report a likely integration problem. Otherwise follow the logged remediation: fix write access and re-run with `--trigger`, or verify a pre-cutoff 👍 manually.
   - **4 PR_NOT_OPEN** — the PR was merged or closed; stop and report.

## Guardrails

- Cap the loop at five rounds without approval, then summarize recurring findings and hand the decision to the user.
- Judge findings on the merits. Disagreement is allowed; ignoring is not.
- Use one ordinary commit per round and no force-pushes.
- Poll politely; do not manually scrape the PR page.
- A late start is fine because freshness is anchored to the push or explicit trigger, not watcher launch time.
- Before ending without approval, preserve unaddressed findings in a focused issue after showing and confirming the payload.
