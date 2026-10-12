# Recovery and limits

Read this when the watcher fails or times out, the round budget may be exhausted, or the session cannot continue.

## What the watcher accepts

The bot keeps one summary comment on the PR that names the commit of its latest review and that review's status. The watcher reads a verdict only while that status is Completed for the expected commit:

- a review by the bot for the full expected SHA, submitted at or shortly before the completion, is findings;
- otherwise a 👍 by the bot on the PR, created no earlier than ten seconds before the completion, is approval;
- with neither visible it keeps waiting. A missing review alone never means approval.

A failed read is tried again and never read as empty; five failed reads in a row end the run with an error. GitHub refusing the target (HTTP 401, 404 or 422) ends it at once. The bot is matched by its exact login, `--bot` to change it.

This protocol is observed, not documented by the bot's vendor. A summary in an unknown form ends the run with an error that prints it. Then read the PR yourself, and merge only on evidence tied to the full SHA.

## Error and timeout recovery

For exit 1, read the message: a usage or target error, a head that moved (restart for the new head), an unknown summary form, or GitHub being unreadable.

For exit 3, the last line says what was seen last:

- **GitHub reports another head:** confirm the push and the target.
- **No summary, or the summary names another commit:** no review of this commit started. Where reviews do not start by themselves and review requests are authorized, run again with `--trigger`.
- **The review is running:** run again with a longer `--timeout`.
- **Completed, and neither a review nor a 👍 is visible:** read the PR's reviews and reactions yourself before running again.
- **The summary is older than the review request:** the requested review did not complete. Do not post another request for the same head.

If a request received no verdict while the head stayed fixed, report the integration failure and stop. Use a local or external replacement review only when the caller selects it; record its full reviewed SHA and apply the same threshold, budget, CI, dispatch, and merge requirements.

## Round budget

Accept `round-budget=<positive integer | unlimited>`, defaulting to `3`. Only an explicit caller choice enables `unlimited`.

Each verdict with remaining blockers for the expected SHA consumes one round. Timeouts and CI failures consume none, but a review after a CI fix counts if blockers remain.

An accepted verdict proceeds through CI and any authorized merge, including on the final permitted round. When blockers exhaust a finite budget, report them and begin no further repair. With `unlimited`, continue until acceptance, PR closure, exhausted timeout recovery, or a decision that needs the owner.

## Handoff

The current agent owns the PR to completion within these gates; waiting is no reason to delegate the loop. Hand off only when the owner requests it or the session cannot continue. Include the verified PR URL and full current head, the goal, constraints and authorization, remaining work, and the consumed and remaining budget. Identify local changes outside that head without altering them. Mark unavailable state as unverified, omit secrets, and link review threads.

A handoff does not launch another agent or grant new rounds, permissions, or a model change.
