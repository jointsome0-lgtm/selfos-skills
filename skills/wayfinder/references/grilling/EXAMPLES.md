# Examples

Short invented transcripts showing the load-bearing rules of the grilling loop. Every name, path, and number below is invented.

## A round asks the whole frontier, answerable by number

Owner: "Grill my plan to split the `parser` module."
The tree so far has three decisions with no unsettled prerequisites, so the first round asks all three:

> ❓ **Q1 — Split axis**: Split by grammar stage or by output type?
>
> ➡️ Grammar stage — the tests already group that way.
>
> ❓ **Q2 — Legacy flag**: Keep the `--compat` flag through the split?
>
> ➡️ Drop it — nothing in this repository references it.
>
> ❓ **Q3 — Migration**: Land the split in one PR or as a sequence?
>
> ➡️ One PR — the module is small enough to review whole.

Owner: "1 yes, 2 keep it — an external script still uses it, 3 yes."
Three branches settle in one exchange; the next round asks only what those answers unblocked.

## Dependent questions never share a round

"Which grammar stages become modules?" depends on Q1 above, so it waits for the round after Q1 is answered — it is never asked alongside Q1 with an "if you said stages, then…" hedge.

## Fact lookup stays inside permitted surfaces and does not stall the round

A frontier question needs the `src/parser/` layout and the open parser issues — facts, so the agent dispatches a background lookup over this repository and its tracker rather than asking the owner. It does **not** open `~/notes/`, the repo's ignored `.env`, or another workspace, even though the filesystem would allow it. While the lookup runs, only the questions downstream of it wait; the rest of the frontier is asked now.

## A decision is never answered by the agent

Agent: "❓ **Q2 — Legacy flag**: Keep the `--compat` flag? ➡️ Drop it — nothing in this repository references it."
Owner: "Keep it; an external script still uses it."
The agent records *keep*. The recommendation never overrides the owner.

## An answer reopens a branch

Owner, after a round: "My answer to 2 changes what 3 should have asked."
The frontier was the agent's judgement, not a computed graph — the agent reopens branch 3 and re-asks it in the next round under the corrected premise.

## Accepted

Owner: "Agreed, grammar stage." → the branch resolves **accepted**; its dependents join the next frontier.

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

The frontier is empty. Owner: "Sounds right, go."
Only now does the calling wrapper skill create the agreed artifact. The primitive itself never writes — it hands confirmed outcomes back to the wrapper.
