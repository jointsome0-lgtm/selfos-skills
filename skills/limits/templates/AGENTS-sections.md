# Sections for the adopting repository's AGENTS.md

Fill `<package>` with the Python package name, then merge these sections into
the repository's agent instructions.

## Purpose

Keep the complete implementation core, including its internal dependencies,
and the contracts, tests, and documentation needed for a change small enough
to reason about together. Leave room for instructions and the work itself.
Read other tests, examples, and reference material when needed. Report core
size, the task's working set, and the repository total as different scopes.
The repository total alone does not establish that the working set is too
large or that the architecture needs simplification.

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

`.github/workflows/limits.yml` runs these checks on every PR.
`scripts/limits.py` handles the repository limits. Ruff and the named test
files are separate steps in the same workflow.

- Budget: the repository's tracked UTF-8 text fits in 70k `o200k_base`
  tokens, counted with `tiktoken` from the Git index. Tests, documentation,
  comments, whitespace, and the copied checker count. `LICENSE`, lock files,
  and binary blobs (NUL bytes or invalid UTF-8) do not; the checker reports
  how many binary files it excludes. Submodule contents are outside this
  repository. This is a conservative CI policy covering all repository
  text. The checker does not select or measure a task's working set. A PR
  that crosses the budget fails even when a smaller working set fits.
  The 70k/30k split is a planning assumption for a 100k window. The other
  30k cover instructions, the task, diff, tool output, and answer.
  The number is never raised in the PR that needs it. A boundary
  becomes a separate repository only after a concrete second subsystem
  exists, both sides run the same executable contract test (schema, types),
  and the complete working set still fits the budget; never a prose boundary.
- Map: one line per directory, at most 250 characters, in `README.md`. The
  script fails on a directory without a line or a line without a directory.
  Hidden directories (harness and CI config) are outside the map.
- Every goal line names its test file and every test file is named by a goal
  line. Adding a test file means adding a goal line, and the PR says why an
  existing test could not be strengthened instead. The checker uses fixed
  `test_*.py` and `*_test.py` filenames under visible directories and requires
  a module-level `test*` function or a `test*` method in a top-level class.
  Pytest determines collection and execution in the workflow.
- Tests reach the system only through its public test API. Python files under
  a `tests/` directory, files matching those test patterns, and `conftest.py`
  may import `<package>.testing`, but no other part of `<package>`.
  Use direct imports or direct loader calls with literal module names.
  Loader aliases declared in imports keep that meaning throughout the file;
  do not shadow them or store or pass a loader for later calls.
- Zero comments and zero docstrings in Python, including inline ones. A CI
  count fails the PR on the first one; only machine markers (`# noqa`,
  `# type: ignore`, shebang) are exempt. A function that needs a paragraph
  needs a better name, a split, or a test. What it does is the code; why is
  the commit.
- No symlinks: every tracked path is a regular file or a submodule.
- No process artifacts in the repository: the only Markdown files are
  `GOALS.md`, `AGENTS.md`, `README.md`, `CLAUDE.md`; any other `.md` fails.
  Scope lives in the issue, findings in the PR, reasons in the commit.
- Format and lint (`ruff`) and the named green tests are limiter steps in
  the same workflow, outside `scripts/limits.py`. The workflow lists the
  test files that must pass, so a goal test can stay red while the code it
  claims is still being built.
