# Examples

Short invented transcripts of grilling an SDD. Every repository, §, decision, and number below is invented. The interview mechanics — one question at a time, a recommendation per question, the terminal states — belong to the `grilling` primitive; what is shown here is the SDD framing and where outcomes land.

## Repository-resolvable fact: looked up, not asked

Owner: "Grill §4 Retry policy."
§4 already caps retries at 3 with backoff, and open issue #212 questions only the backoff base. The agent does not ask "how many retries do you want?" — §4 answers that. First question instead: "§4 fixes the cap but not the backoff base; issue #212 proposes 2 s. Recommendation: accept 2 s — the §9 latency budget allows it."

## Implementation detail already fixed by a §

Owner: "Should exporter files be one-per-format?"
Agent: "§6 Module layout already fixes one module per export format — this is not an open trade-off. Citing §6; there is nothing to decide unless you want to reopen that §."

## Canon contradiction: framed with both owning §§

Agent: "§3 Ingestion says records are immutable after intake; §8 Corrections describes in-place edits. That is a contradiction between §§, not a fact I can resolve. Which rule owns record mutability? Recommendation: §3 owns it, and §8 becomes an append-only corrections stream."
Owner: "Agreed, §3 owns it."
**accepted** → one change: §8 rewritten to the corrections stream, plus the Decision Log line
`- 2042-08-11 — Records stay immutable (§3); corrections become an append-only stream (§8). Rejected: in-place edits — they break §3's replay guarantee. #214`

## Genuine owner trade-off

Agent: "§7 leaves snapshot retention undecided. 30 or 90 days? Recommendation: 30 — nothing in this repository reads snapshots older than 21 days."
Owner: "90; the auditors asked for a full quarter."
**accepted as amended** — the SDD edit and the log line record 90 with the audit reason, and the rejected 30 is noted because the auditor constraint is load-bearing for future retention questions.

## Deferred lands as an issue only after the draft is confirmed

Owner: "Defer §10 encryption-at-rest until we pick a storage provider."
Agent: "Deferring with that trigger. Draft issue: 'Decide §10 encryption-at-rest — revisit trigger: storage provider chosen.' Publish it?"
Owner: "Yes." → **deferred**; the issue is created now — after the confirmation, never before.

## Blocked names the missing artifact

Agent: "§5's queue sizing has no throughput measurement anywhere in this repository — the branch is **blocked** on that number. Smallest resolving issue drafted: 'Measure intake throughput on the demo corpus (feeds §5).' Publish?"
Owner: "Go."
The issue is published; §5 itself stays untouched until the number exists. The agent does not invent one to finish the interview.

## Editorial correction versus owner trade-off

§2's summary table shows "excluded" where §2's own prose and every surrounding rule say "included" — canon already fixes the desired state. Interactively, the agent proposes the one-cell correction and applies it on confirmation. Non-interactively, it remains a proposed diff in the output; nothing is written.

## Non-interactive run: drafts only, repository untouched

The same grilling of §§ 3, 7, and 10 with no owner present ends with the decision tree, one recommendation per open branch, the proposed §8 diff, exact Decision Log wording, and both issue drafts — and a clean `git status`, no issue created, no log line added. Filing the unresolved retention question as an issue would be action; it does not happen.

## Interactive run: nothing lands before the final confirmation

Owner: "The corrections-stream design sounds right."
Agent: "Landing it: the §8 edit plus the log line above in one change — confirm?"
Owner: "Confirmed."
Only now is the file edited. "Sounds right" alone was not the confirmation.
