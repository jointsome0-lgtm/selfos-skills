# Sections for the adopting repository's AGENTS.md

Fill `<package>` with the Python package name, then merge both sections into
the repository's agent instructions.

## Three sources of truth, one each

- The past: git. Every commit says why, not just what. A commit without a
  reason does not merge. There is no decision log; `git log` is the log.
- The present: the code. There is no design document. If the code and a text
  disagree, the text is wrong.
- The future: `GOALS.md`. Direction, invariants, base state. Every line
  names its test; a line without a test does not enter.

Read in this order: `GOALS.md`, the map in `README.md`, the issue or PR you
are on, then code and tests. Before changing a thing, `git log -S<term>`: the
reason it is the way it is lives there, not in a file.

## Limiters (numbers checked in CI, not conventions)

All of them live in one script, `scripts/limits.py`, run by
`.github/workflows/limits.yml` on every PR.

- Budget: the whole repository fits in 70k tokens (bytes ÷ 4), counting
  every tracked file except `LICENSE` and lock files. There are no generated
  or vendored files; the first one that appears is excluded in the same PR,
  with its reason in the commit. A PR that crosses the budget fails. The
  other 30k of a 100k window are the task, the diff, tool output and the
  answer. The number is never raised in the PR that needs it. A boundary
  becomes a separate repository only after a concrete second subsystem
  exists, both sides run the same executable contract test (schema, types),
  and the complete working set still fits the budget; never a prose boundary.
- Map: one line per directory, at most 250 characters, in `README.md`. The
  script fails on a directory without a line or a line without a directory.
  Hidden directories (harness and CI config) are outside the map.
- Every goal line names its test file and every test file is named by a goal
  line. Adding a test file means adding a goal line, and the PR says why an
  existing test could not be strengthened instead.
- Tests reach the system only through its public test API: the only
  `<package>` import allowed in `tests/` is `<package>.testing`.
- Zero comments and zero docstrings in Python, including inline ones. A CI
  count fails the PR on the first one; only machine markers (`# noqa`,
  `# type: ignore`, shebang) are exempt. A function that needs a paragraph
  needs a better name, a split, or a test. What it does is the code; why is
  the commit.
- No process artifacts in the repository: the only Markdown files are
  `GOALS.md`, `AGENTS.md`, `README.md`, `CLAUDE.md`; any other `.md` fails.
  Scope lives in the issue, findings in the PR, reasons in the commit.
- Format and lint (`ruff`) and the named green tests are limiter steps in
  the same workflow, outside `scripts/limits.py`. The workflow lists the
  test files that must pass, so a goal test can stay red while the code it
  claims is still being built.
