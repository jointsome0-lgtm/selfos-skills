# Claude Fable 5.1

Sources: Anthropic's [Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1) and the cross-model [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices). Checked against upstream 2026-09-01.

Also covers Claude Mythos 5.1 (same underlying model). Fable 5 prompts carry over unchanged, so read [claude-fable-5.md](claude-fable-5.md) first: everything there still applies unless a section below replaces it. On conflict with the core skill, this file wins.

## Effort

Upstream default is `high`; re-run the effort sweep even if you ran one on Fable 5, because level names do not map to the same amount of thinking across models. Gains over Fable 5 show at every level and are largest at the top. `medium` roughly matches Fable 5 at lower cost, and `low` often beats Opus and Sonnet models on cost per task while scoring higher, so put Fable 5.1 at `low` in the comparison wherever you would otherwise run a smaller model at a higher effort. The core skill's ceiling of `high` for delegated runs still applies.

Two effort-specific behaviors:

- **At `low` it searches less** and answers from memory more than Fable 5. For lookup or research delegations, raise effort for those turns, or add to the system prompt:

```text
When a query centers on a name you do not confidently recognize, or recognize from a fast-moving area like AI models and developer tools where the landscape shifts within months, the name itself is the thing to verify: search before answering, and include the name as the user wrote it in at least one query alongside any reformulations. This holds even when you have some background on it — partial background is exactly what makes an out-of-date answer sound authoritative, so familiarity is not a reason to skip the search.
```

- **At `xhigh` and `max`** (owner-requested design passes only) it may draft a long deliverable in thinking and then write it again, doubling the turn. Prefer `high` for long deliverables. If a higher tier is measured to help, set `max_tokens` with room for both, and append to the user message, replacing `[max_tokens]` with the real value:

```text
Everything produced in one reply, including any reasoning or drafting it does before the reply, counts toward a single limit of about [max_tokens] tokens. If that limit is reached before the reply is finished, the person receives a cut-off response and has to start over. Composing an entire output or deliverable in full as reasoning and then again as a reply would double the length of the turn without improving the result, so don't do that.

Instead, when the person has asked for a long or effort-intensive deliverable such as a multi-section document, a large table or dataset, or a complete code file, spend extra effort on understanding the request, checking the inputs the answer depends on, settling the structure and other difficult decisions, and otherwise using the reasoning space to reason and the output space to write an output. Usually it is not needed to draft an output multiple times.
```

## Progress updates: quieter than Fable 5

It writes fewer user-facing updates during long tool-calling turns, more so at higher effort and in longer chains: minutes of silence, or a final message covering only the last step. Fix in this order:

1. If you own the harness, confirm updates arrive at all: between-call notes come back as `thinking` blocks that are empty under the default `thinking.display` of `"omitted"`; set `display: "updates"` (beta header `thinking-display-updates-2026-08-18`) or `"summarized"`.
2. Remove legacy lines that suppress narration, such as "hold all findings for the final response".
3. Only then add a line saying when you want text and what it should contain. For a subagent whose final message is the deliverable, the closing recap is the part that matters:

```text
Before you start, say in a line what you're about to do; brief updates while you work help the user follow along. Close with a short recap that stands on its own — what you found, what you did, and what's next — so a reader who only sees the last message has the full picture.
```

If the product hides tool output, say so, or it will run commands to "show" output nobody sees: "Only you see that command's output — the user's terminal shows at most a few lines of it. If the user needs to read any of it, put it in your reply."

## Batch independent tool calls

Explicitly requested fetches go out in parallel as expected. In coding and computer-use loops, where the next independent calls are implied rather than named, it may issue one per turn. Each extra turn costs a round trip, not quality. Add after the current request:

```text
First privately list what you need next; then request every item that doesn't depend on another's result in this one response.
```

In an API harness, append this as a turn-scoped system message (`role: "system"`, `clear_at: "next_user_message"`, beta header `mid-conversation-system-clear-at-2026-08-21`) after each tool-result user message, or without the beta as a text block after the `tool_result` blocks. Append a fresh copy each turn and leave earlier copies untouched: deleting or rewriting them edits history (see next section).

## Append-only history and compaction

Harness authors only. Thinking blocks are bound to the exact conversation that produced them: for accounts created on or after 2026-08-31, replaying one after its prefix changed returns a 400 (or drops the block with `thinking.block_binding.prefix_mismatch_behavior: "drop_block"`, beta header `thinking-binding-controls-2026-08-01`). Later models will enforce this for everyone. Send per-turn reminders as turn-scoped system messages, change instructions or tools through mid-conversation system messages rather than by rewriting `system` or `tools`, and let server-side compaction or context editing do the trimming. Client-side compaction should replace the whole history with one summary message plus the new user turn, replaying nothing else; cache reads are cheaper now, so try later compaction points. It responds well to being told what the summary must keep:

```text
Summarize the transcript inside <summary></summary> tags. Include relevant information in the summary such that this conversation will be continued by a new context window without needing to redo work or be reprovided with relevant constraints or context. Be sure to preserve: (1) any difficulties or problems that came up, and how they were handled or resolved; (2) any possibilities, options, or approaches that were raised, tried, or set aside, and why; (3) anything that was asked for, decided, agreed, ruled out, or established as a preference, constraint, or boundary — stated exactly; (4) exactly where things stand now — what has been covered, settled, or completed so far; (5) anything still open, unresolved, promised, or expected to happen next; (6) specific details that would be hard to reconstruct — names, numbers, dates, exact wording, links or references — kept exactly. Be complete on these even at the cost of length; keep everything else concise. Weight the two voices differently: keep what the user said, asked for, shared, or established carefully and close to their own words; your own explanations and reasoning can be condensed much further, to what they concluded or produced — as long as nothing in the six items above is dropped.
```

## Writing: density, formatting, quoting

- **Denser prose than Fable 5**: longer sentences, fewer paragraph breaks, though fewer stock phrases and less jargon overall. Define the anti-pattern, preferably in a user message; the short form "Please remove all mannered prose." also tends to work:

```text
Mannered prose substitutes metaphor and flourish for direct statement. Instead of "a parameter worth varying," the mannered writer produces "a dial worth turning." Instead of "this point still matters," they write "this point earns its keep." The phrases exist to display the writer, not to convey the idea, and readers can tell. That is why mannered prose irritates: it makes the reader work harder so the writer can perform. It is also imprecise. Metaphors drag in connotations the writer did not choose and cannot control. The fix is to say what you mean. When a literal phrase is available, use it.
```

- **Less formatting in chat, not more**: it uses bold less and reaches for headers, lists, and quotation marks less often than earlier models. Remove anti-formatting rules written for those models, or replace them with a rule that says when formatting is appropriate:

```text
Use lists and bullet points when asked to, or when the content is multifaceted enough that they help with clarity. If the person explicitly requests minimal formatting, always format your responses without bullet points, headers, lists, or bold emphasis, as requested. In conversational, personal, or emotional exchanges, keep to plain prose.
```

- **Unmarked quotation** when summarizing documents: more likely than Fable 5 to reproduce source passages without marking them. Fix with one complete example in the system prompt (the request, the response, and a `<rationale>` sentence saying why it is correct), showing each source conveyed in a sentence or two of indirect speech with at most a short marked phrase quoted. Write tool calls in the example as your own tool's output, so they read as templated output rather than literal text to emit.

## Finish the whole task

Replaces the "early stopping" snippet in the Fable 5 reference. On long asynchronous work it sometimes narrates the next step instead of doing it ("Next, I'll …") or asks permission for a step the request already covered ("Shall I apply this?"). Two system-prompt blocks together fix this; apply both, or only the first when length is tight. For autonomous runs, use the first as the prompt's autonomy boundary, but its "destructive actions or genuine scope changes" clause is narrower than the core skill's policy, so keep the core's confirmation categories: right after the opening sentence, which carries much of the effect and stays as written, add "Require confirmation for external writes, destructive actions, purchases, or a material expansion of scope." plus any product-specific gates. Trade-off: the block also asks less about ambiguous requests, so check that on your own tasks.

```text
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Offering follow-ups after the task is done is fine; asking permission before doing the work is not.

Exception: when the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.

Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll…', 'let me know when…'), do that work now with tool calls. That includes retrying after errors and gathering missing information yourself. Do not stop because the context or session is long. End your turn only when the task is complete or you are blocked on input only the user can provide.

Before running a command that changes system state (such as restarts, deletes, or config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

```text
# Delivering work
The user's request — or the plan they approved — sets the scope, and the scope is the deliverable: don't quietly narrow, widen, or swap it. Read ambiguity the way a careful colleague would: make routine judgment calls yourself, and check in only when different readings would lead to materially different work. If you see a real problem with the task as specified, say so in a sentence or two and keep building under stated assumptions; if the user hears the concern and reaffirms, that is their decision, so deliver the full request.

If a question comes up partway, first do everything that doesn't depend on the answer; then state the assumption you made, or — when going ahead on a wrong guess would be unsafe or would make the work useless — put the question at the end of a turn that also delivers that progress. If one part turns out to be blocked, complete every other part in full and say exactly what you left out and why — the whole task is the deliverable, and scaling it down is the user's call, not yours. A step you have decided on is something to run, not to announce: describing the next step and ending the turn leaves it undone until the user replies.

Keep changes to what the request needs. Something else you notice worth doing — cleanup or documentation the task didn't call for, a change to a file the task didn't require — is a suggestion to make at the end, not a change to make; actions clearly beyond what the ask implies, and risky or destructive ones, still need the user's go-ahead.
```

## Scope, tests, and edit size

- **Extras and test sprawl**: on open-ended features it may fix nearby code, extend unmentioned behavior, or commit more test files than the change warrants. This instruction cuts both substantially with no measured loss in task success. Its ambiguity sentence sets a lower bar than the "Delivering work" block above: always take the most direct reading, versus ask when readings would lead to materially different work. A prompt that carries both needs one threshold. For an autonomous run with nobody to answer, keep this sentence and drop the check-in clause from "Delivering work"; for a human-in-the-loop run, replace this sentence with "Where the task is ambiguous, follow the Delivering work rule above."

```text
If, while working or testing, you find a pre-existing bug, a performance concern, or behavior the task doesn't mention, don't fix, optimize or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up in your summary. Where the task is ambiguous, implement the reading its wording and the surrounding code most directly support, state that assumption in your summary, and don't build for the other readings as well. Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the task asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files — roughly one focused test per stated behavior — and don't turn scratch checks into additional permanent test files. This is about extras only: implement every behavior the task asks for, completely.
```

- **Whole-file rewrites**: more likely than Fable 5 to rewrite a file for a small change. Same result, more output tokens and time. Append to the system prompt or first user message: "The number of tokens used to edit files is best minimized, all else being equal. Therefore, when it will not affect the end result, try to surgically edit a file rather than rewrite the entire thing."

## Safeguard false positives

Fewer than Fable 5 at launch, and finding vulnerabilities in source code is permitted. A blocked request still returns `stop_reason: "refusal"`. Three known triggers: compile-check phrasing (ask "Are there any bugs in this program?" rather than "Does this compile without errors?"); lesser-known programming languages (give context on the language, such as access to its documentation); base64-encoded data in tool output (remove it from the model's context).

## Subagents and vision

- **Lead keeps working while subagents run**: if the harness allows it, do not force the lead to block on each subagent. Have the spawn tool return immediately, deliver results in a later user message, and give the lead a separate wait tool. The lead still often chooses to wait; the savings come from the runs where it carries on. Time to completion drops at similar quality and cost.
- **Vision**: on dense charts and images it does its best work when it can crop, zoom, and re-check. Run it as an agent with a container holding the raw images and basic image libraries (PIL, OpenCV), or at minimum provide a crop tool that returns an enlarged region; that alone delivers most of the uplift.
