---
name: grilling
description: Use when the owner explicitly asks to grill a plan or decision, conduct a decision interview, or invokes $grilling. Do not select for routine implementation, fixes, reviews, or explanations merely because they involve design choices.
compatibility: Requires read access to owner-scoped sources. No specific CLI or OS; network, write access, and external integrations are needed only when the chosen facts or an owner-confirmed outcome require them.
metadata:
  selfos.version: "1.0.0"
---

Start on an explicit interview request, including natural-language requests such as "grill this plan before implementing". An explicitly requested wrapper whose workflow includes this contract may use it without a second `$grilling` invocation. A design choice in otherwise authorized work is not an interview request.

Map the subject as a **design tree** of decisions and their prerequisites. Work through it with the owner until you reach a shared understanding. Provide a recommended answer for every question; the owner makes the decisions.

## Rounds and the frontier

The **frontier** contains every decision whose prerequisites are settled. Ask the whole frontier in one **round**, then wait for the owner's answers. Dependent questions wait for a later round; never ask them alongside their unresolved prerequisites.

Number questions so the owner can answer "1 yes, 2 the second option". Separate questions with a horizontal rule:

```
❓ **Q1 — <question title>**: <question body; may run several paragraphs or offer choices>

➡️ <your recommended answer>

---

❓ **Q2 — <question title>**: <question body>

➡️ <your recommended answer>
```

Recompute the frontier after each round. If an answer changes another question's premise, reopen that branch in the next round. The frontier is your judgment, not a computed graph. Honor an owner's request for one question at a time.

## Facts versus decisions

Look up discoverable **facts** in this repository, its issue tracker, and roots and tools explicitly allowed by the owner or runtime. Repository instructions may narrow access, never widen it. This skill grants no access to home directories, unrelated workspaces, private journals, ignored paths, credentials, or ambient agent state.

Run lookups in the background where supported and authorized, including a subagent when available. Treat each running lookup as an unsettled prerequisite: only its dependent questions wait; ask the rest of the frontier now.

Put **decisions** to the owner and wait for the answer.

## Terminal states

A branch of the decision tree may end:

- **accepted** — the owner confirmed the recommended or amended choice;
- **rejected** — the owner declined it;
- **deferred** — postponed, with an explicit revisit trigger;
- **blocked** — stopped on a named missing fact or artifact.

Deferred and blocked are resolved states only after the owner confirms the reason and the trigger. Do not force a decision merely to finish the interview.

## No action before confirmation

An empty frontier ends questioning. Finish only when the owner confirms shared understanding. Until then, inspect permitted facts and present drafts only: do not create or edit issues, specs, decision logs, code, or other durable artifacts. Non-interactive runs stop at drafts and never publish decision-bearing artifacts.

## Composing with wrappers

Use a domain wrapper as the entry point when one covers the subject; otherwise use this skill directly. The wrapper owns its scope, context sources, and where confirmed outcomes land. It follows this interview contract without restating it. This skill grants no write authority. Legacy wrappers keep their existing rules until they adopt this contract.

Worked examples: [EXAMPLES.md](EXAMPLES.md).
