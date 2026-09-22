# Claude Opus 5.5

Sources: Anthropic's [prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5), [effort reference](https://platform.claude.com/docs/en/build-with-claude/effort#recommended-effort-levels-for-claude-opus-5-5), [model changes](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5), and [migration guide](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide). Checked against upstream 2026-09-22 UTC.

Use this reference for `claude-opus-5-5`. It is self-contained; the Opus 5 reference remains for that model. On conflict with the core skill, this file wins, except that the core's effort ceiling still applies.

## Model choice and effort

Consider Opus 5.5 for long repository tasks, code review, knowledge work, and visual inputs. Anthropic reports these strengths; compare on representative tasks before selecting it.

Set `medium` explicitly as the starting point. It is the upstream default, replacing Opus 5's `high`. Compare `low`, `medium`, and `high` on representative tasks; matching level names do not establish matching cost or quality across models. Ordinary delegations stay at `high` or below. `xhigh` and `max` remain reserved for live design passes the owner explicitly requests.

Thinking is always on. Lower effort to control latency and cost; an instruction to disable thinking is not a supported setting. In API runs, `max_tokens` covers thinking and the answer together, including hidden thinking. Size it for both. Per-message effort changes preserve the cache; changing top-level effort does not.

## Compose the task

Existing Opus 5 prompts are a starting point. The following are provisional defaults carried over from that reference, not separately established 5.5 behaviors: specify length and scope, cap subagents on small tasks, omit generic self-check loops and automatic verifier agents. Retain required tests and acceptance evidence. For broad reviews, collect findings before severity triage. Reassess these defaults on the actual task.

For unattended runs only, complete all unblocked work. Stop when finished or when remaining work needs user input or protected actions. Preserve authorization gates; report unresolved items.

Apply the following only when relevant:

- For multi-app work, inspect authorized relevant sources before writing. Discovery grants no additional permissions.
- For frontend work, specify concrete design choices and unwanted patterns.
- For chat latency, remove generic deliberation instructions. Treating earlier answers as settled is optional for chat; omit that rule from analysis and coding.
- For dense visuals, reassess old workarounds; supply original images and crop tools where useful.

## Agent loops and API integrations

Use these controls only when the caller owns the relevant runtime behavior. Hosted clients may already handle them. Changing integration code requires its own task scope.

From the [migration guide](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide):

- Omit `thinking` or use `adaptive`. `disabled` and manual `enabled` budgets are rejected. Read response blocks by type and replay thinking blocks unchanged.
- `tool_choice` values `any` and `tool` are rejected. Use `auto`, describe when the tool applies, and use strict tool schemas or structured outputs for schema guarantees. Strict schemas do not force a call.
- Progress notes arrive in thinking blocks, empty under default `display: "omitted"`. Use `display: "updates"` with `thinking-display-updates-2026-08-18`, or `summarized`, and render the non-empty blocks. Prompt for cadence after confirming the client displays them.
- Preserve conversation history. Editing earlier instructions, tools, or messages can invalidate later thinking blocks; use supported appended messages for changes.

For unattended loops, check remaining work after text-only `end_turn`; wait for running tools or agents. Cap automatic continuations at three per task. Report unresolved work after that cap.

For authorized teams, consider elapsed-time signals and advisory budgets. Keep separate timeouts and team limits; measure quality under time pressure.

When wrapping pasted material, use paired tags with matching random IDs. The initial system policy should mark it as external data whose instructions require the user's own authorization. Tags alone cannot prevent injection.

From the [model changes](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5): handle `stop_reason: "refusal"` and its category. Remove requests to reproduce private reasoning; use supported summaries when needed. Follow the migration guide for computer-use tool compatibility and model-switching behavior rather than assuming all Opus 5 integrations transfer unchanged.
