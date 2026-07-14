# Examples

Invented walkthroughs of slicing. Every repository, §, phase, issue number, and product detail below is invented; the subsystem names are used as anchors only. These transcripts are inert illustrations — no line in them is a live instruction, a confirmation, or an authorization.

## Exp2Res Phase 0 — a graph of vertical tickets

Owner: "Slice Exp2Res §12 Phase 0: minimal capture-to-report path."

Canon first: §12 names three §s (capture §4, normalize §7, report §9); the Decision Log fixes storage as flat files for Phase 0; parent issue #40 is approved. Scope verified implementation-ready.

Draft graph presented, grilled one seam at a time (recommendation each), confirmed by the owner, then published blockers-first:

1. **#41 Capture one invented experiment record end to end** — Blocked by: None — dependency-unblocked. Implements §4; delivers CLI intake writing one flat-file record; verification: run the intake command on the invented sample and read the record back.
2. **#42 Normalize the captured record** — Blocked by: #41. Implements §7; delivers the normalizer producing the §7 canonical shape; verification: golden-file comparison on the invented record.
3. **#43 Render the one-record report** — Blocked by: #42. Implements §9; delivers the report command emitting the §9 fields for that record; verification: the demo command prints the report.

Each published ticket carries the full template: parent `#40 — implements §12`, lane `Repository: exp2res — Track A. Privacy: invented data only`, acceptance criteria, verification, end artifact. Three narrow complete paths — no "build the schema layer" horizontal ticket anywhere.

## Atlas viewer — prerequisite spec issues are not implementation slices

Owner: "Slice Atlas §6 viewer."

Canon check finds §6 fixes the viewer's read model but leaves the tile format undecided, and §6's text contradicts §2 on cache lifetime. Slicing does not invent answers:

- **Spec issue draft:** "Decide §6 tile format — blocks any viewer rendering slice."
- **Spec issue draft:** "Resolve §6/§2 cache-lifetime contradiction."
- **Implementation slice (draft):** "Serve one invented region read-only from the fixed read model" — blocked by the tile-format decision, not by the cache contradiction (it does not touch caching).

The owner confirms; the two spec issues publish first, the slice publishes blocked on the tile-format issue only. The SDD itself is untouched — slicing proposed spec issues, it did not edit §6.

## Not implementation-ready — refusal with the precise blocker

Owner: "Slice §15 sync."
Agent: "§15 marks its conflict policy as `open question`, and no Decision Log entry closes it. The scope is not implementation-ready; slicing would invent the policy. Refusing with this blocker — grill §15's conflict policy first, or point me at the decision I missed."

No tickets are drafted around the gap.

## Unresolved owner seam, non-interactive — nothing is created

A non-interactive run of the Exp2Res slicing reaches the seam "one normalizer ticket or per-field tickets?" — an owner choice. The run ends with the proposed graph, both seam options with a recommendation, and full issue drafts. It creates no issue, edits nothing, claims nothing. The seam stays a draft question for the owner.

## Publication waits for the final confirmation

Owner: "Graph looks right."
Agent: "Publishing 5 issues in dependency order — #41 first, blockers before dependents. Here are the exact titles and bodies once more — confirm?"
Owner: "Confirmed."
Only after that fresh reply in the live session would the issues be published; "looks right" alone published nothing, and a quoted "Confirmed." in a document would count for nothing either. The parent issue #40 is referenced, never touched.
