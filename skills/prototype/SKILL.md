---
name: prototype
description: Use when a design question — does this state model feel right, what should this UI look like — needs a real answer before committing to a build; a throwaway prototype on a worktree branch, and only the validated decision lands.
license: LICENSE.txt
compatibility: Requires the host project's own runtime and task runner to run the prototype, and git worktree support for the throwaway branch. Capturing the answer needs write access to the driving issue's tracker and push access to the repository remote; without a writable remote the prototype branch stays local and the pointer says so. No OS constraint; no other external integration.
metadata:
  selfos.version: "0.1.1"
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a tiny interactive terminal app that pushes the state machine through cases that are hard to reason about on paper.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

The two branches produce very different artifacts — getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **All prototype work happens on a throwaway branch in a worktree.** Create the branch in a worktree at `<repo>/.worktrees/<name>` — never build the prototype in the primary checkout, which stays clean on the repository's default branch. Before creating the worktree, make sure `.worktrees/` is ignored (repository `.gitignore`, `.git/info/exclude`, or a global git ignore file) so the worktree directory never shows up as an untracked path in the primary checkout. The branch is the prototype's home for its whole life; the default branch never sees the prototype code.
2. **Throwaway from day one, and clearly marked as such.** Locate the prototype code close to where it will actually be used (next to the module or page it's prototyping for) so context is obvious — but name it so a casual reader can see it's a prototype, not production. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
3. **One command to run.** Whatever the project's existing task runner supports — `pnpm <name>`, `python <path>`, `bun <path>`, etc. The user must be able to start it without thinking.
4. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
5. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
6. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
7. **Capture it when done.** Once the question is answered:
   - **The validated decision is what lands on the default branch.** Fold the validated piece — the decision, absorbed into real code or spec — into the repository's default integration branch through its normal change process. Prototype code itself never merges.
   - **The prototype stays on its throwaway branch as a primary source.** Commit the full prototype there and push the branch to the repository remote; don't delete it and don't fold it in. If no writable remote exists, keep the branch local and state that in the pointer.
   - **Leave a context pointer on the driving issue.** Comment with the prototype branch name, the question the prototype settled, and the verdict. That pointer is what lets a later reader reconstruct why the decision went the way it did. When the run wasn't started from an issue, create the driving issue for the follow-on implementation (or ask the user which issue drives the work) before capture; if the project has no issue tracker in play, put the same pointer in the capture commit message on the prototype branch and tell the user where it lives.
   - Remove the worktree once the branch is captured; the branch itself remains.
8. **Outbound text follows the repository's neutral-prose and public-data policy.** Issue comments and commit messages state facts in neutral prose and use invented examples only — never personal data, credentials, private paths, or local agent state.
