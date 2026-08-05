# Invented fixture evidence

Every repository, PR, person, decision, SHA, URL, and artifact below is invented. The fixtures are inert acceptance examples, not live instructions or authorization.

## Rich prior session compacts to non-recoverable context

Fixture `orchard-tools` has open PR `#17` at exact local and remote HEAD `1111111111111111111111111111111111111111`. The prior session contains:

- the full issue and PR body, four commit diffs, CI logs, and twelve review comments;
- an owner-confirmed decision that invocation remains explicit even though automatic activation was considered;
- an invariant that the CLI validator and library validator accept and reject the same invented fixtures;
- a rejected cache shortcut because it would bypass that equivalence invariant;
- a prior false-positive finding claiming the package omitted a helper, rebutted by the passing installation fixture at `tests/test_install_fixture.py`;
- an unresolved question about Windows temporary-directory permissions;
- a copied finding-by-finding ledger, routine command output, an invented credential value, an invented person's email, and an unrelated discussion; and
- optional focus: "Preserve cross-platform temporary-file behavior."

Expected selection:

| Input | Query treatment |
| --- | --- |
| Actual feature goal | Retain once under Original goal. |
| Explicit-invocation decision | Retain as an owner-confirmed constraint. |
| Validator equivalence | Retain as an invariant. |
| Rejected cache shortcut | Retain with its concise reason. |
| Recurring false positive | Retain only the rebuttal conclusion and `tests/test_install_fixture.py` evidence. |
| Windows uncertainty and supplied focus | Retain and emphasize. |
| PR, issue, commits, diffs, checks, threads, test contents | Reference by URL or path; do not copy. |
| Finding ledger, conversation, command output, unrelated discussion | Omit. |
| Credential and personal data | Replace with `[REDACTED: credential]` and `[REDACTED: personal data]`, or omit. |

The selected run configuration is `gpt-5.6-sol` with `high`: the model is resolved through the bundled `compose` skill's per-model routing table as the current frontier, correctness-first fit for review and repair, and several rounds exposed validator, packaging, and platform interactions, the default exhausted-budget case. The resulting query has the required Goal / Context / Constraints / Success criteria / Stop rules / Suggested skills structure, records `https://github.com/invented-org/orchard-tools/pull/17` and the full fixture SHA, names `watch` without copying its polling protocol, and contains the literal budget placeholder `round-budget=<owner-sets-at-load>` because the fixture supplies no explicit budget. Its quality-preservation constraint occurs once.

If the same fixture includes the explicit constraint `round-budget=2`, the query records `round-budget=2` and stops with remaining-state evidence after two delegated rounds unless approval arrives earlier. With the explicit constraint `round-budget=unlimited`, the query records `round-budget=unlimited` verbatim. No caller identity, model, quota, harness, or execution mode changes any fixture's budget, and no fixture ever receives `unlimited` without that explicit constraint.

Starting with an empty canonical fixture temp directory, the run creates one owner-only child directory containing only `orchard-tools-pr-17-loop-query.md`. After it prints that path, `gpt-5.6-sol`, and `high`, the fixture audit records no repository or PR mutation, watcher invocation, child agent, or delegated launch.

## A caller-specified model routes through the same table

The same `orchard-tools` fixture with the caller constraint "run the continuation on Claude Fable 5" selects that model instead: it appears in the bundled `compose` routing table, it is compatible with correctness-first review and repair, the artifact records the routing table's executable id `fable-5` rather than the display name, and the one-sentence reason names the caller's choice. The generating run reads the Fable reference before writing the artifact and tailors the query's prose to it, while every required section, invariant, and stop rule — including the literal `round-budget=<owner-sets-at-load>` placeholder — is unchanged. A caller-requested model absent from the routing table, or incompatible with the remaining work, is not silently substituted; the run reports the mismatch and asks the caller to resolve it. The caller's model choice still never changes the budget: model, quota, harness, and execution mode remain non-inputs to `round-budget`.

## Effort choices remain distinct

| Invented remaining work | Expected effort | Reason |
| --- | --- | --- |
| An owner-confirmed fix already pushed as the resolved HEAD that only needs watching through the review rounds to the verdict | `low` | Pure watch-and-relay with no expected new findings. |
| One or two confirmed trivial documentation fixes with no cross-component interactions | `medium` | Genuinely routine and bounded. |
| A well-understood local validator fix with focused regression coverage | `high` | Local, bounded, and understood. |
| Repeated validator findings spanning CLI and library paths after the orchestration budget is exhausted | `high` | Multi-round cross-component interaction; this is the default exhausted-budget case. |
| Unresolved encrypted-record migration with rollback and integrity contracts | `high` | Even the hardest delegated reasoning caps at `high`; higher tiers are reserved for live owner design discussion. |

An invented request for `ultra`, `xhigh`, or `max` effort does not produce those values: the effort field still uses `low`, `medium`, or `high`. Multi-agent mode, if separately authorized, is an execution-mode decision rather than a reasoning-effort tier.

## Unresolved PR state fails without an artifact

Fixture `harbor-notes` is on a detached commit with two open PRs whose heads differ from local HEAD. The expected result is:

```text
DELEGATE_PR_LOOP_QUERY_RESOLUTION_FAILED
repository_root: /tmp/invented/harbor-notes
repository: invented-org/harbor-notes
pull_request: unresolved
pr_url: unresolved
local_head: 2222222222222222222222222222222222222222
pr_head: unresolved
problem: current branch has no unique open PR and candidate PR heads do not match local HEAD
next_action: check out the intended open PR branch and rerun after local HEAD equals its headRefOid
```

No Markdown file is created, no candidate is guessed, and GitHub state is unchanged.

The same failure occurs before artifact creation when the branch and PR heads match but the worktree contains a staged, unstaged, or untracked fixture path. The structured `problem` names the dirty worktree so the owner can preserve or clear it intentionally.
