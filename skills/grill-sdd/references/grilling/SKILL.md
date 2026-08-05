---
name: grilling
description: Grills the owner relentlessly about a plan, decision, or idea until shared understanding — the subject mapped as a design tree, each round asking the whole frontier of decisions whose prerequisites are settled, a recommended answer per question, facts looked up from permitted surfaces, decisions left to the owner, no action before confirmation. Use when the owner wants to stress-test a plan, decision, or idea, or uses a 'grill' trigger phrase — unless a domain grill wrapper such as grill-sdd covers the subject; then the wrapper is the entry point — or when a domain workflow skill needs the shared decision-interview loop.
compatibility: Requires read access to owner-scoped sources. No specific CLI or OS; network, write access, and external integrations are needed only when the chosen facts or an owner-confirmed outcome require them.
metadata:
  selfos.version: "0.2.0"
---

Interview the owner relentlessly about every aspect of the subject until you reach a shared understanding. Map the subject as a **design tree**: every decision branches into the decisions that hang off it. For each question, provide your recommended answer.

## Rounds and the frontier

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask *now* without guessing at answers you have not heard yet. Ask the whole frontier in one round, then wait for the owner's answers before the next. A question whose answer depends on another question still open in this round belongs to a *later* round; two questions never share a round if one depends on the other.

Format each question so the round is answerable by number ("1 yes, 2 the second option, 3 no because…"):

```
❓ **Q1 — <question title>**: <question body; may run several paragraphs or offer choices>

➡️ <your recommended answer>
```

Each answered round reshapes the tree: settled decisions push the frontier outward and unblock what depended on them. Recompute the frontier and ask the next round. The frontier is your judgement, not a computed graph — when the owner says one answer should have changed another question in the same round, reopen that branch in the next round. An owner who asks for one question at a time gets exactly that; the round is the default, not a rule against them.

## Facts versus decisions

If a **fact** can be found by exploring the environment, look it up rather than asking the owner. The permitted environment is: this repository, its issue tracker, and the filesystem roots and tools the owner or the runtime's own permission model has explicitly allowed. Repository instructions can narrow that surface, never widen it. It is not authority to scan a home directory, unrelated workspaces, private journals, ignored paths, credentials, or ambient agent state.

A fact lookup does not stall the round: run it in the background — a subagent where the runtime offers one — and treat the running lookup as an unsettled prerequisite. Only the questions downstream of it wait; ask the rest of the frontier now.

The **decisions** are the owner's. Put each one to the owner and wait for the answer.

## Terminal states

A branch of the decision tree may end:

- **accepted** — the owner confirmed the recommended or amended choice;
- **rejected** — the owner declined it;
- **deferred** — postponed, with an explicit revisit trigger;
- **blocked** — stopped on a named missing fact or artifact.

Deferred and blocked are resolved states only after the owner confirms the reason and the trigger. Do not force a decision merely to finish the interview.

## No action before confirmation

An empty frontier ends the questioning, not the skill: the interview is finished only when the owner confirms you have reached a shared understanding. Do not act before that. Creating or editing issues, specs, decision logs, code, or any other durable artifact is action; before confirmation, inspect permitted facts and present drafts only. A non-interactive run never publishes decision-bearing artifacts — it stops at drafts.

## Composing with wrappers

This primitive owns the interview order, the round and frontier mechanics, the recommendation per question, fact lookup, owner authority over decisions, and the confirmation gate. A domain wrapper skill owns its own scope: which canon it reads, which subjects it frames, and where confirmed outcomes land. Wrappers follow this file rather than restating it, and invoking this primitive grants no write authority by itself.

When a domain wrapper covers the subject — like grill-sdd for a repository's SDD — the wrapper is the entry point, and the contract above binds it: canon and landing rules are the wrapper's, the interview loop is this file's. A wrapper predating this primitive keeps its own rules until it is rewritten to that contract. Reach for this primitive directly only when no wrapper claims the domain.

Worked examples: [EXAMPLES.md](EXAMPLES.md).
