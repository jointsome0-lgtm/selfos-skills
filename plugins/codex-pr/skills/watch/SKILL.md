---
name: watch
description: Watches an open PR after each push, waits for the Codex cloud review verdict, and iterates fixes in-session until approval. Use when the user asks to babysit a PR, watch or wait for the Codex review, or run the push-review-fix loop.
---

Babysit the current PR through Codex review rounds: wait for the verdict, apply fixes, push, repeat — all in one session, no manual polling of the PR page.

Background: on every push to an open PR the Codex bot reacts 👀 on the PR body, reviews, then either reacts 👍 (all clear) or posts a review with inline comments (findings). The watcher script encapsulates this protocol.

## Protocol (one round)

1. Make sure the round's work is committed and pushed to the PR branch.
2. Run the watcher in the background when the agent environment supports it, or run it in the foreground and wait:

   ```
   ../../scripts/codex-pr-watch.sh
   ```

   The script path is relative to this skill folder. Defaults: current repo, the current branch's PR, expected head = local `git rev-parse HEAD`, poll every 30 s, timeout 25 min. See `--help` for flags (`--pr`, `--repo`, `--trigger`, …).
3. Act on the exit code:
   - **0 APPROVED** — 👍 from the review bot. Report the clean verdict to the user; the loop is over.
   - **2 FINDINGS** — stdout carries the review body plus every inline comment as `path:line`. Read them all. Fix each finding, or — if after honest consideration you disagree — rebut it explicitly in your round summary; never silently drop one. Then commit (per the repo's commit conventions), push, and start the next round at step 2.
   - **3 TIMEOUT** — no verdict arrived. Re-run once with `--trigger` (posts an "@codex review" comment). If it times out again, stop and tell the user.
   - **4 PR_NOT_OPEN** — the PR was merged or closed meanwhile; stop and report.

## Guard-rails

- Cap the loop at **5 rounds** without approval; then stop, summarize what keeps coming back, and hand the decision to the user.
- Judge findings on the merits — the reviewer is sometimes wrong. Disagreeing is allowed; ignoring is not.
- No force-pushes mid-loop: one ordinary commit per round keeps review rounds mapped 1:1 to commits.
- The watcher polls politely (30 s) and needs no manual PR-page polling. Run it in the background when the agent environment can surface completion; otherwise wait for it in the foreground.
- If the loop must end before a clean verdict (deadline, "merge now"), file the last round's unaddressed findings as an issue before merging. Cutting the loop short is allowed; losing its findings is not.
