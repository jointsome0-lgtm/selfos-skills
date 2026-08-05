# Claude Opus 5

Sources: Anthropic's [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) and the cross-model [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices). Checked against upstream 2026-08-04.

On conflict with the core skill, this file wins.

## Profile

Strongest on difficult agentic coding — multi-file features, larger refactors, end-to-end work — completing full tasks rather than leaving stubs, and best when given the complete specification up front and left to run. Code review has high precision and recall that holds at lower effort, supporting a fast pass now and a thorough pass later. Long-context behavior stays consistent across the 1M-token window, and it coordinates subagent teams well (effective writer–verifier patterns). Runs well out of the box on Opus 4.8-era prompts; in our harness it runs via the Agent/Workflow `model` parameter.

- Review prompts: do not write "only report high-severity issues" or "be conservative" — it follows that literally and under-reports. Ask it to report everything and filter in a separate pass.

## Effort

Upstream default is `high`; `low` and `medium` produce strong quality at a fraction of the tokens and latency — use them liberally as the primary cost/latency control wherever quality holds, and re-run an effort sweep rather than carrying defaults over from a prior model. (Upstream suggests `xhigh` for demanding work; the core skill's operating ceiling of `high` for delegated runs applies.) Effort controls how much it thinks, not how much it says — lowering effort does not reliably shorten visible responses.

## Verbosity — prompt for length explicitly

Default responses, agentic narration, and written files all run longer than prior Opus models. Each has its own lever:

- Conversational responses: "Keep responses focused, brief, and concise. Keep disclaimers short and spend most of the response on the main answer." In a long system prompt, repeat a one-line reminder near the end.
- Agentic narration: describe the cadence — "Before your first tool call, say in one sentence what you're about to do. While working, give a brief update only when you find something important or change direction. When you finish, lead with the outcome." Positive examples of the style you want beat lists of don'ts.
- Written deliverables (reports, Markdown files): "Match document length to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate."

## Over-verification and scope — remove, don't add

Opus 5 verifies and self-corrects without being told. **Remove explicit verification instructions** ("include a final verification step", "use a subagent to verify", "double-check your answer") and legacy harness verification scaffolding: they compound with the model's own behavior and add cost with no quality gain. This is the direct opposite of the GPT-5.6 guidance to include a check-your-work criterion — a flagship example of why per-model references override the core.

It can also expand task scope on its own judgment. For narrow tasks:

```text
Deliver what was asked, at the scope intended. Make routine judgment calls
yourself, and check in only when different readings of the request would lead
to materially different work. If the request seems mistaken or a better
approach exists, say so in a sentence and continue with the task as asked.
```

To keep correction narration to corrections that matter: "Only correct an earlier statement when the error would change the user's code, conclusions, or decisions; for slips that change nothing, make the fix and move on."

## Subagent spawning — cap it

It delegates readily; delegation pays on genuinely independent, sizeable tracks but multiplies cost on small tasks. Give explicit criteria or deterministic caps:

```text
Delegate to a subagent only for large tasks that are genuinely independent
and parallelizable. Do not delegate work you can finish yourself in a handful
of tool calls, and do not use subagents to verify your own work. If one
subagent can complete the task, use one, and keep spawn counts low.
```

## Running with thinking disabled

Thinking is on by default and can be disabled only at effort `high` or below. Prefer keeping thinking enabled and controlling cost with lower effort — thinking on at `low` usually beats thinking off at similar cost. With thinking disabled, two artifacts can appear: tool calls written as user-facing text (the call never runs and the leaked text pollutes later turns), and internal XML tags leaking into output. If thinking must stay off, remove any "do not think/reason" rules (they increase tag leakage) and add the combined mitigation — general form only, naming thinking tags specifically makes it less effective:

```text
When you use a tool, you may say a brief sentence first. If no tool can
express what the user asked for, say so instead of guessing. Do not include
internal or system XML tags in your response.
```
