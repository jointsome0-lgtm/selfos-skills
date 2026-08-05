# Examples

Short invented transcripts showing the load-bearing rules of the grilling loop. Every name, path, and number below is invented.

## Fact lookup stays inside permitted surfaces

Owner: "Grill my plan to split the `parser` module."
The agent looks up the `src/parser/` layout and the open parser issues in this repository — those are facts. It does **not** open `~/notes/`, the repo's ignored `.env`, or another workspace, even though the filesystem would allow it.
First question: "Split by grammar stage or by output type? Recommendation: grammar stage — the tests already group that way."

## A decision is never answered by the agent

Agent: "Keep the legacy `--compat` flag? Recommendation: drop it — nothing in this repository references it."
Owner: "Keep it; an external script still uses it."
The agent records *keep*. The recommendation never overrides the owner.

## Accepted

Owner: "Agreed, grammar stage." → the branch resolves **accepted**; the agent moves to the next dependent decision.

## Rejected

Owner: "No renaming of public functions in this pass." → the branch resolves **rejected**; dependent rename questions are dropped, and the reason is kept for the summary.

## Deferred requires a trigger

Owner: "Defer the streaming API."
Agent: "Until what? Recommendation: revisit when the batch API ships."
Owner: "Yes." → **deferred**, with an owner-confirmed revisit trigger. Without the trigger the branch would still be open.

## Blocked names the missing fact

Agent: "I cannot recommend a cache size — no production traffic number exists anywhere in this repository. The branch is **blocked** on that measurement."
Owner confirms; the branch rests until the number exists. The agent does not invent one to finish the interview.

## Non-interactive run: drafts only

The same interview started with no owner present produces a decision tree, recommendations, and draft issue texts in the session output — and creates no issue, edits no file, publishes nothing.

## Confirmation before write

Owner: "Sounds right, go."
Only now does the calling wrapper skill create the agreed artifact. The primitive itself never writes — it hands confirmed outcomes back to the wrapper.
