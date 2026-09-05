# <project>

Long term: <where this is going, one paragraph>.

Short term: <the current target, one paragraph>.

Rules of this file:

- Use plain `N. text` paragraphs, with the test path on that line or an
  indented continuation. A blank line ends the goal.
- Put examples in fences or HTML comment blocks starting a line with at
  most three leading spaces. Inline comment markers remain ordinary text.
- A line below exists only if it has a test. Growing this file costs a test.
- A test sees the system only through the public API and `<package>.testing`.
  It knows nothing about tables, modules or repositories.
- There are exactly as many test files as lines below. A new file needs a new
  line, and the PR says why an existing test could not be strengthened.
- Tests belong to goals, not to code. Code without a test is normal; a test
  without a goal line is not. A test freezes behaviour, so a wrong test freezes
  a mistake: when the goal moves, change the test, and add a file only when no
  existing test can carry the claim.

## Invariants

1. <a property that must never break, stated so a test can check it>
   `tests/test_<invariant>.py`

## Base state

2. <the path that must keep working end to end>
   `tests/test_<journey>.py`

## Non-goals

<What this project will not do, so nobody builds it.>

## Deferred

<What waits, and the concrete failure that would fetch it.>
