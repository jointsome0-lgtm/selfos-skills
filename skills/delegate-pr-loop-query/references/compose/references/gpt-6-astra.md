# GPT-6 Astra

Sources: OpenAI's [GPT-6 Astra model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra), which carries the model's prompting guidance; there is no separate prompting guide. Checked against upstream 2026-09-04.

Applies to `gpt-6-astra` — in the Codex CLI, Codex cloud, or the API (Responses API; Chat Completions works but without tool calling). At the check date it was rolling out to enterprises in the Trusted Access Program, with API and plan access announced for the following days. GPT-6 Astra supports the same API capabilities as GPT-5.6 (computer use, Structured Outputs, streaming, Programmatic Tool Calling, multi-agent orchestration, prompt caching, persisted reasoning, compaction, pro mode), and the lean, outcome-first prompt style carries over, so read [gpt-5.6.md](gpt-5.6.md) first: everything there still applies unless a section below replaces it. On conflict with the core skill, this file wins.

## Initiative and follow-through

Stays coherent on long tasks better than GPT-5.6 Sol, and is designed to ask when more input could materially change the result — so it asks for clarification where earlier models assumed and persisted, and it may stop where you expected it to make reasonable assumptions and carry on. It also asks non-blocking questions while working by default; for a subagent whose final message is the deliverable, nobody answers those, so decide the autonomy level up front. Three upstream blocks, in escalating order; the first replaces the GPT-5.6 reference's "the core skill's compact autonomy policy is enough":

- **Bias toward action.** Use as the prompt's autonomy boundary. Its "clearly destructive or irreversible" clause is narrower than the core skill's policy, so keep the core's confirmation categories: append "Require confirmation for external writes, destructive actions, purchases, or a material expansion of scope." plus any product-specific gates.

```text
You should infer the user's intent and task scope from the instructions and prior conversation context. Your job is to bias towards action and carry the user's intended task to completion.

When the user expresses intent to perform new work or fix an existing issue, persist until the user's intended goal is complete. Progress autonomously towards the user's goal (e.g. creating isolated worktrees / checkouts if needed, resolving merge conflicts, read-only actions, creating draft PRs etc.) unless they are clearly destructive or irreversible.
```

- **Treat a request as an instruction.** Add when it stops at acknowledging capability or proposing a plan on prompts phrased as "can you…", "help me…":

```text
When the user's prompt indicates a request for action, such as "can you...", "I want to...", "help me..." and similar expressions, treat these as instructions to do the work and take action. Do not stop at acknowledging capability (e.g. "Yes…"), proposing a plan, or offering to continue. Do not settle for a partial or "helpful enough" solution that does not fully satisfy the user's task to save time, effort or tokens. If a task requires sustained work, complete all the necessary work until the intended outcome is fulfilled.
```

- **Ask only with a reviewable result in hand.** Add when it blocks on approval before doing the work it could already do; upstream reports quicker completion with this block. Its last sentence removes unsolicited approval flows — if the product needs a gate the upstream text waives (say, before merging), state that gate explicitly right after it.

```text
Before asking the user clarifying questions, you should complete the work that is already authorized from context and necessary to make the proposed action concrete and reviewable. The user should be approving a concrete, reviewable result. For example, before deploying a change, writing to an external application, merging a PR or publishing a site, do all the required work first so that user approval is the final step. You don't need user permission for reversible tasks, read-only actions, reviews or fixes, or anything for which authorization is provided earlier in the session or strongly implied from the task instruction.

Do not introduce unsolicited warnings, disclaimers, approval flows, or safety/compliance checklists due to hypothetical risk.
```

## Instruction following

Follows longer instructions better than earlier models and is more sensitive to everything in context: skill files, AGENTS.md, and similar instruction files can steer it, and unclear or conflicting guidance in one of them can make it pause and block early. Audit every instruction file the run can read for lines that could redirect it, and make precedence explicit:

```text
The user's instructions take precedence over guidelines provided in a skill. If explicit user instructions conflict with a skill's instructions, prioritize the user's instructions.
```

When it pauses or changes direction for no visible reason, have it name the cause; this also surfaces silent and conflicting guidance when a harness loads many skills and instruction files:

```text
If a skill causes you to ask for permission or confirmation, pause, leave requested work unfinished, or diverge from the user's intent, name and link to the exact SKILL.md file you read, quote the relevant instruction, and briefly explain how it applies. Distinguish explicit skill requirements from your interpretation of guidelines.
```

## Writing style

Tends toward detailed, formatted answers — lists, tables, Markdown — and may reuse the same phrases across sessions. The GPT-5.6 reference's "drop bare 'be concise'" advice still holds; instead specify the style and structure the deliverable needs. Upstream blocks, each usable alone:

- Prose over formatting:

```text
Default to using clear, concise paragraphs, each developing one main idea. Use lists only when the information is genuinely parallel, sequential, or easier to compare, and avoid nested lists unless the hierarchy cannot be expressed clearly in prose. Use plain, simple language: familiar words, concrete examples, and precise verbs. Prefer active voice and direct statements.

Make sure to state the main point clearly and early, then develop it with the explanation and detail the reader needs. Let each sentence build on what came before. Develop the points that matter and provide enough support to be useful.
```

- Technical communication calibrated to the reader:

```text
Use plain language over jargon, and reference technical details only to the degree that it helps illustrate an idea or your work to the user. Communicate complex concepts in a clear and cohesive manner, and calibrate your writing to the level of background knowledge assumed from the user's prompt and context.
```

- Stock phrases and invented labels:

```text
Avoid using slop words or phrases like "Bottom Line:" in conclusions, "delve," "foster," "leverage," "it's worth noting," "importantly," "Question? Answer." or "This isn't about X. It's about Y.", "genuinely" or hyphenated compound descriptions and adjectives. Do not use concluding summary statements such as "In short:..", "The simplest mental model is:...".

State the intended action directly. Avoid adding what you won't do, what will remain unchanged, or how you'll separate or categorize results. Do not use contrastive framing such as "X, not Y" or "X—not Y" that introduces an unprompted alternative that the user didn't ask about. Avoid invented compound labels like "exact-head checks" and "editorial-row layouts", vague qualifiers, and canned transitions; use plain verbs and prepositions to state the actual relationship directly.
```

## Subagent delegation

Trained to divide work across parallel subagents, but delegates less often than most multi-agent harnesses want, and responds well to being told when and how much to delegate. In a harness with collaboration tools, start from:

```text
If at any point you can parallelize work by delegating tasks to another agent (no matter if you are the root or subagent), you should do so using collaboration tools if it could save time or improve quality.
```

Inter-agent messages may carry grammar or spacing errors. When a human reads them:

```text
Messages that you send to other agents and your final answer may be read by a human, so ensure they are legible. Always put proper spaces between words and/or numbers.
```

## Testing and verification

Thorough in testing before it calls a coding task done — on small tasks, broader than the change warrants, or the same checks repeated. The GPT-5.6 reference's single check-your-work criterion still belongs in the prompt; bound it so it scales with the change:

```text
Do not write tests for reversible, low-impact changes that mirror the implementation. If you do choose to verify your work with tests, make sure that the tests are meaningful and necessary to verify implementation.

Run tests appropriate to the change and complete required checks. Once those pass, broaden or repeat testing only when new changes, failures, or unresolved concerns justify it; otherwise, continue toward completing the task.
```

## Model and effort choice

One variant, `gpt-6-astra`, for the hardest delegated work: computer use, browsing, software engineering, long multistep workflows across code, browsers, and professional software. Upstream reports stronger results on several evaluations with substantially fewer output tokens, so the estimated cost per task can be lower than GPT-5.6 despite the higher per-token price — compare per task, not per token, when choosing between them.

- Reasoning effort `none` is not supported. Migrating from `none` or `minimal`, start at `low` and compare; otherwise keep the current effective effort. The core skill's ladder (`low`–`high`, `medium` as the default) applies.
- To change effort mid-conversation, add a `configuration_update` input item rather than changing the request-level `reasoning.effort`; the update holds until the next one and preserves the cached prompt prefix. Standard single-agent requests only; check upstream compatibility limits before adopting it.
- Pro mode (`reasoning.mode: "pro"`) carries over from GPT-5.6, with the same rule: same outcome-first prompt, no "think harder" prose.
- Fast mode (`service_tier: "fast"`) has no latency SLA on GPT-6 Astra and, like `"priority"`, is unavailable with EU data residency, where Standard processing is the only option.
- Effort, mode, and service tier belong in config or API parameters, not in prompt prose.

## Migrating a GPT-5.6 prompt

Eval-driven and incremental, as in the GPT-5.6 reference: switch the model with the prompt unchanged, baseline, then fix one measured regression at a time. Codex can apply the recommended changes with the OpenAI Docs skill: `$openai-docs migrate this project to GPT-6 Astra`.

- Set `model` to `gpt-6-astra`. Remove `temperature`, `top_p`, and `top_logprobs`; in Chat Completions also `logprobs`, in Responses also `message.output_text.logprobs` from `include`.
- Tool calling requires the Responses API; move Chat Completions integrations that call tools.
- Coming from GPT-5.5 or earlier, replace `prompt_cache_retention` with `prompt_cache_options.ttl` set to `"30m"`, and review the prompt-caching changes (cache boundaries, cache-write billing).
- The most likely regression is unnecessary approval pauses; fix it with the initiative blocks above before touching anything else. Then check formatting, delegation rate, and test breadth against the sections above.
- Async tool calling (`async: true` on a function or custom tool, result returned later under the original `call_id`), mid-turn steering over WebSocket, and misalignment monitoring are integration features, not prompt text; see the official guide.
- Security-adjacent work: state the defensive purpose and authorization up front, as for GPT-5.6. GPT-6 Astra adds asynchronous misalignment monitoring that can trigger alerts; it is a safeguard on the run, not a prompt surface.
