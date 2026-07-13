---
name: grilling
description: Grills the owner relentlessly about a plan, decision, or idea until shared understanding — one decision-tree branch at a time, a recommended answer per question, facts looked up from permitted surfaces, decisions left to the owner, no action before confirmation. Use when the owner wants to stress-test a plan, decision, or idea, or uses a 'grill' trigger phrase — unless a domain grill wrapper such as grill-sdd covers the subject; then the wrapper is the entry point — or when a domain workflow skill needs the shared decision-interview loop.
---

Interview the owner relentlessly about every aspect of the subject until you reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one by one. For each question, provide your recommended answer.

Ask questions one at a time, waiting for the owner's feedback on each before continuing. Asking multiple questions at once is bewildering.

## Facts versus decisions

If a **fact** can be found by exploring the environment, look it up rather than asking the owner. The permitted environment is: this repository, its issue tracker, and the filesystem roots and tools the owner or the runtime's own permission model has explicitly allowed. Repository instructions can narrow that surface, never widen it. It is not authority to scan a home directory, unrelated workspaces, private journals, ignored paths, credentials, or ambient agent state.

The **decisions** are the owner's. Put each one to the owner and wait for the answer.

## Terminal states

A branch of the decision tree may end:

- **accepted** — the owner confirmed the recommended or amended choice;
- **rejected** — the owner declined it;
- **deferred** — postponed, with an explicit revisit trigger;
- **blocked** — stopped on a named missing fact or artifact.

Deferred and blocked are resolved states only after the owner confirms the reason and the trigger. Do not force a decision merely to finish the interview.

## No action before confirmation

Do not act until the owner confirms you have reached a shared understanding. Creating or editing issues, specs, decision logs, code, or any other durable artifact is action; before confirmation, inspect permitted facts and present drafts only. A non-interactive run never publishes decision-bearing artifacts — it stops at drafts.

## Composing with wrappers

This primitive owns the interview order, the recommendation per question, fact lookup, owner authority over decisions, and the confirmation gate. A domain wrapper skill owns its own scope: which canon it reads, which subjects it frames, and where confirmed outcomes land. Wrappers follow this file rather than restating it, and invoking this primitive grants no write authority by itself.

When a domain wrapper covers the subject — like grill-sdd for a repository's SDD — the wrapper is the entry point, and the contract above binds it: canon and landing rules are the wrapper's, the interview loop is this file's. A wrapper predating this primitive keeps its own rules until it is rewritten to that contract. Reach for this primitive directly only when no wrapper claims the domain.

Worked examples: [EXAMPLES.md](EXAMPLES.md).
