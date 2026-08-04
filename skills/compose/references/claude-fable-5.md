# Claude Fable 5

Sources: Anthropic's [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5) and the cross-model [Claude prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices). Checked against upstream 2026-08-05.

Also covers Claude Mythos 5 (same underlying model). On conflict with the core skill, this file wins.

## Profile and task sizing

Fable 5 is built for problems previously too complex, long-running, or ambiguous: multiday goal-directed runs with strong instruction retention, first-shot correctness on complex well-specified problems, high bug-finding recall in review and debugging, dense-image vision, and dependable dispatch and supervision of parallel subagents. Delegate at the top of your difficulty range — have it scope, ask clarifying questions, and execute; testing it only on simpler workloads undersells its range. Not for offensive cybersecurity or biology/life-sciences work: safety classifiers target those domains (plus extraction of summarized thinking) and can return `stop_reason: "refusal"`, occasionally on benign adjacent work — state the defensive purpose up front and configure fallback to Claude Opus 4.8 where the harness supports it.

## Turn shape and harness

Individual turns on hard tasks run many minutes at higher effort; autonomous runs extend for hours. Size client timeouts accordingly and prefer checking on runs asynchronously over blocking. To keep it from overplanning on ambiguous tasks:

```text
When you have enough information to act, act. Do not re-derive facts already
established in the conversation, re-litigate a decision the user has already
made, or narrate options you will not pursue in user-facing messages. If you
are weighing a choice, give a recommendation, not an exhaustive survey.
```

In our harness, Claude models run via the Agent/Workflow `model` parameter; effort follows the core skill's operating canon. Upstream recommends `high` as the default with `xhigh` for capability-sensitive workloads — the operating ceiling of `high` for delegated runs still applies; lower effort settings on Fable 5 remain strong. To prevent unrequested tidying at higher effort:

```text
Don't add features, refactor, or introduce abstractions beyond what the task
requires. Don't design for hypothetical future requirements: do the simplest
thing that works well. Only validate at system boundaries (user input,
external APIs); trust internal code and framework guarantees.
```

## Steering: brief beats enumerated

Instruction-following is strong enough that one short instruction replaces enumerating behaviors. For output shape:

```text
Lead with the outcome: your first sentence should answer "what happened" or
"what did you find". Supporting detail and reasoning come after. Keep output
short by being selective about what you include, not by compressing the
writing into fragments, abbreviations, or jargon.
```

For checkpoints in long workflows:

```text
Pause for the user only when the work genuinely requires them: a destructive
or irreversible action, a real scope change, or input that only they can
provide. If you hit one of these, ask and end the turn, rather than ending on
a promise.
```

And for scope discipline (it can occasionally take unrequested actions):

```text
When the user is describing a problem or asking a question rather than
requesting a change, the deliverable is your assessment — report findings and
stop. Before running a command that changes system state, check that the
evidence actually supports that specific action.
```

## Ground progress claims

On long autonomous runs, instruct it to audit progress against actual tool results — in Anthropic's testing this nearly eliminated fabricated status reports:

```text
Before reporting progress, audit each claim against a tool result from this
session. Only report work you can point to evidence for; if something is not
yet verified, say so explicitly. If tests fail, say so with the output; if a
step was skipped, say that.
```

## Subagents, memory, long runs

- **Subagents**: it dispatches parallel subagents readily and manages long-running ones well. Say when delegation is appropriate, prefer asynchronous communication over blocking on each return, and favor long-lived subagents that keep context across subtasks: "Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track."
- **Verification**: separate fresh-context verifier subagents outperform self-critique on long builds — "establish a method for checking your own work at an interval of X, verifying with subagents against the specification."
- **Memory**: it performs notably better with a place to record lessons across runs — one lesson per file with a one-line summary; record corrections and confirmed approaches with the why; update rather than duplicate; delete notes that prove wrong.
- **Early stopping**: deep into long sessions it can end a turn on a statement of intent without the tool call, or ask permission it does not need. For autonomous pipelines add: "You are operating autonomously; the user cannot answer mid-task. For reversible actions that follow from the original request, proceed without asking. Before ending your turn, check your last paragraph — if it is a plan, a question, or a promise about work you have not done, do that work now."
- **Context-budget anxiety**: avoid surfacing remaining-token countdowns; if the harness must, add "You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits."

## Intent, readability, mid-run messaging

- **Give the reason, not only the request**: "I'm working on [the larger task] for [who it's for]; they need [what the output enables]. With that in mind: [request]."
- **Final-message readability**: after long agentic stretches, ask for the final message as a re-grounding, not a continuation — outcome first, complete sentences, no working shorthand, arrow chains, or self-invented labels; identifiers each get a plain-language clause.
- **send-to-user tool**: for long asynchronous agents, provide a client-side tool that displays a message verbatim without ending the turn (deliverables, precise progress numbers, direct answers). Tool inputs are never summarized. Pair it with explicit elicitation ("when you have content the user must read verbatim, call send_to_user") — defining the tool alone is not enough — and forbid routing narration through it.

## Migrating prompts and skills

- Skills and prompts written for prior models are often too prescriptive for Fable 5 and can degrade output; re-evaluate which instructions, tools, and guardrails are still needed before adding new ones.
- **Never instruct it to echo, transcribe, or explain its internal reasoning in the response** — that triggers the `reasoning_extraction` refusal category and elevated fallbacks. Audit legacy "show your thinking" instructions when migrating; read structured thinking blocks or use a send-to-user tool instead.
