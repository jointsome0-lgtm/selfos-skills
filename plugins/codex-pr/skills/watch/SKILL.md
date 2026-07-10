---
name: watch
description: After pushing to an open PR, wait for the Codex cloud review verdict and iterate fixes in-session until it approves. Use when the user asks to babysit a PR, watch/wait for the Codex review, or run the push→review→fix loop.
---

Babysit the current PR through Codex review rounds: wait for the verdict, apply fixes, push, repeat — all in one session, no manual polling of the PR page.

Background: on every push to an open PR the Codex bot reacts 👀 on the PR body, reviews, then either reacts 👍 (all clear) or posts a review with inline comments (findings). The watcher script encapsulates this protocol.

## Protocol (one round)

1. Make sure the round's work is committed and pushed to the PR branch.
2. Run the watcher in the background, so the session picks up the moment the verdict lands (in Claude Code: Bash with `run_in_background: true`; in other harnesses: their background-run equivalent, or just run it and wait):

   ```
   <plugin-root>/scripts/codex-pr-watch.sh
   ```

   `<plugin-root>` is `${CLAUDE_PLUGIN_ROOT}` when installed as a Claude Code plugin, or `plugins/codex-pr/` in a clone of this repository. Defaults: current repo, the current branch's PR, expected head = local `git rev-parse HEAD`, poll every 30 s, timeout 25 min. See `--help` for flags (`--pr`, `--repo`, `--trigger`, …).
3. Act on the exit code:
   - **0 APPROVED** — 👍 from the review bot. Report the clean verdict to the user; the loop is over.
   - **2 FINDINGS** — stdout carries the review body plus every inline comment as `path:line`. Read them all. Fix each finding, or — if after honest consideration you disagree — rebut it explicitly in your round summary; never silently drop one. Then commit (per the repo's commit conventions), push, and start the next round at step 2.
   - **3 TIMEOUT** — no verdict arrived. Re-run once with `--trigger` (posts an "@codex review" comment). If it times out again, stop and tell the user.
   - **4 PR_NOT_OPEN** — the PR was merged or closed meanwhile; stop and report.

## Guard-rails

- Cap the loop at **5 rounds** without approval; then stop, summarize what keeps coming back, and hand the decision to the user.
- Judge findings on the merits — the reviewer is sometimes wrong. Disagreeing is allowed; ignoring is not.
- No force-pushes mid-loop: one ordinary commit per round keeps review rounds mapped 1:1 to commits.
- The watcher polls politely (30 s) and needs no babysitting itself: launch it, end the turn if there is nothing else to do, and continue when its completion wakes the session.
