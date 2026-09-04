# Provenance for skills/limits

The checker and templates are adapted from a private repository owned by the
same copyright holder, where they survived their first adoption cycle. The
private locator and paths are omitted; the opaque Git pins remain auditable
by the owner.

## skills/limits/scripts/limits.py

| Field | Value |
| --- | --- |
| Source repository | Private, owner-controlled; locator omitted |
| Source blob | `241bce37cebe4baa496508e983c7d02d32e967a0` |
| Source commit | `d3a385021d17243eec257e7c712cd953393ced4c` |
| Imported | 2026-08-30 |
| License | Apache-2.0 upstream (notice below) |
| Status | **adapted** |

Named deviations; everything else is the upstream script statement for
statement, reformatted per deviation 12:

1. The repository root comes from `git rev-parse --show-toplevel` instead
   of the script's own location, so the copy runs from wherever it is
   installed.
2. The hardcoded package name and its `.testing` allowance become
   `sys.argv[1]`, and the budget accepts an optional `sys.argv[2]`
   override; a missing package prints usage and exits 2.
3. Repository-relative paths use `PurePosixPath` and file reads pass
   `encoding="utf-8"`, so regexes, map comparison, and decoding behave the
   same on Windows.
4. The `## Map` section is located by a complete heading line, not a
   substring.
5. The test detector accepts pytest-style class methods, not only
   top-level functions.
6. A tracked symlink is an error, and the checker never reads through one,
   so its reads stay inside the repository.
7. `npm-shrinkwrap.json` joins the lock-file exclusions.
8. Git paths decode with `errors="surrogateescape"`, so a tracked filename
   with non-UTF-8 bytes does not abort the checker.
9. A missing `## Map` heading in `README.md` is an error of its own, even
   when the repository has no visible directories.
10. A plain `import <package>.testing` without an alias counts as importing
    `<package>`, because that is the name it binds; only the aliased form
    passes the gate.
11. Fenced code blocks (backtick or tilde, indented up to three spaces)
    are ignored when discovering goals in `GOALS.md` and when locating the
    `## Map` heading in `README.md`.
12. The copy is formatted with `ruff format`, so the ruff limiter the
    workflow template documents passes on the shipped file.
13. Every list item in the `## Map` section is format-checked, including
    the first item when the repository has no visible directories.
14. HTML comments are ignored when locating and reading the `## Map`
    section, so a commented heading cannot shadow the live section.
15. The token budget sums the index's Git blob sizes in one
    `git cat-file --batch-check` call, so checkout transformations do not
    change the result.
16. HTML comments are ignored when discovering numbered goals, so hidden
    examples do not bind tests.
17. A blank line followed by an indented continuation stays inside its
    numbered goal entry, allowing ordinary multi-paragraph list formatting.
18. A literal `__import__("<package>.testing")` without a nonempty
    `fromlist` counts as exposing `<package>`, matching Python's return
    value.
19. Only line terminators are removed from `git rev-parse` output, so a
    repository root ending in a space remains intact.
20. Goal discovery accepts both Markdown ordered-list delimiters and up to
    three leading spaces before the marker.
21. The repository root uses filesystem decoding, preserving non-UTF-8
    bytes on POSIX.
22. Bare static and dynamic imports within a dotted package argument count
    as exposing that package root.
23. Dynamic import checks read the callable's module-name argument, and a
    literal relative `import_module` call is resolved against its package.
24. An ATX or Setext heading ends a numbered goal entry.
25. An ATX or Setext heading ends the `## Map` section.
26. Gitlinks are excluded from Python, Markdown artifact, and test
    inspection; a required Markdown file cannot be a gitlink.
27. A sibling unordered-list item ends a numbered goal entry.
28. Test definitions are discovered from the Python syntax tree, not raw
    source text.
29. A Map line's description must contain a non-whitespace character.
30. Required Markdown symlinks are rejected without reading their targets.
31. Missing `README.md` and `GOALS.md` files are reported as problems
    instead of being read.
32. Goal entries use their marker's content indentation, so nested lists
    stay inside the goal while sibling blocks end it.
33. A thematic break ends the Map without being mistaken for a Setext
    heading or hiding the preceding Map line.
34. Root-level pytest module names join the goal and import checks.
35. Pytest-style module names below any visible directory join the goal and
    import checks, matching recursive collection outside `tests/`.
36. A literal `__import__` preserves the full module name only when its
    `fromlist` is statically known to be nonempty; computed values are treated
    as potentially empty and exposing the package root.
37. Every nonblank line in the Map section is validated, including prose and
    non-hyphen list items before the first valid directory entry.
38. Only Git's single trailing LF is removed from the repository root, so a
    POSIX path ending in a newline or carriage return remains intact.
39. Python sources are decoded through Python's tokenizer rules, including
    UTF-8 BOM handling, before token and syntax inspection.
40. Relative static imports from tests inside the checked package are rejected
    conservatively instead of disappearing as an empty module name.
41. A goal marker's complete prefix determines tab stops for its content
    indentation.
42. Setext heading text accepts at most three leading spaces, so indented code
    cannot hide an invalid Map line.
43. A closing Markdown fence must use only the opening fence character and be
    at least as long as the opener.
44. Raw HTML blocks are removed before Map and goal discovery.
45. The adopting AGENTS template separates script checks from the Ruff and
    named-test steps that run directly in the workflow.
46. The import gate covers every Python file below a `tests/` directory, not
    only pytest-style filenames.
47. Every pytest-style module participates in goal comparison, while a
    separate check rejects modules that define no collectable test.
48. The workflow template grants its token read-only repository contents
    access before it runs code from a pull request.
49. Aliases imported for `import_module`, `importorskip`, and `__import__` keep
    their dynamic-import meaning during inspection.
50. Test discovery accepts module-level functions and methods on collectable
    test classes, but not functions nested in helpers or classes.
51. A bare ordered-list marker starts a goal whose content continues on the
    following indented line.
52. Diagnostics render paths and imported names with escaped ASCII
    representations, so control characters cannot forge output lines.
53. Duplicate goal names are counted once in linear time.
54. Goal entries are de-indented by their outer list marker before nested
    Markdown is stripped, so fenced examples inside list items cannot name a
    test.
55. Test discovery honors a module or test class that sets pytest's `__test__`
    marker to a false constant.
56. Four-space indented code blocks are removed after a goal's outer list
    indentation, so example paths do not bind tests.
57. Test discovery honors false `__test__` assignments on candidate functions
    and methods.
58. `unittest.TestCase` subclasses with test methods count even when their
    class names do not start with `Test`.
59. Dynamic loader calls are recognized through imports and their aliases,
    not by an unrelated object's method name.
60. Pytest configuration that overrides `python_files` is rejected, keeping
    goal and import checks aligned with the default module-name patterns.
61. Pytest-style classes that define `__new__` do not count as collectable.
62. Goal continuation tabs expand to Markdown tab stops before the outer list
    indentation is removed.
63. Dynamic loader names and module receivers resolve to the closest lexical
    binding at each call site.
64. A backtick fence opener is ignored when its info string contains a
    backtick, as required by CommonMark.
65. A recognized dynamic loader with a nonliteral module argument fails closed
    because the checker cannot prove that it stays outside package internals.
66. Pytest-style classes inherit the `__init__` and `__new__` collection checks
    through local base classes.
67. Lexical name bindings are indexed once per syntax tree and searched by
    position, avoiding a full scope traversal for every call.

## skills/limits/templates/

| Field | Value |
| --- | --- |
| Source repository | Private, owner-controlled; locator omitted |
| Source commit | `d3a385021d17243eec257e7c712cd953393ced4c` |
| Goal-rule commit | `c75c71b41f56033d623b0087b55ddf5eef6dbe10` |
| Imported | 2026-08-30 |
| License | Apache-2.0 upstream (notice below) |
| Status | **adapted** |

The "Three sources of truth" and "Limiters" sections, the rules of
`GOALS.md`, and the workflow shape are upstream text with the project name,
package, and project-specific goals generalized to placeholders, plus one
added limiter bullet for the ruff and named-test steps that live outside
the script. Workflow action references are pinned to immutable commits at
the named releases.

## Downstream license notice

The upstream repository uses Apache-2.0 at the pinned commit. Its copyright
holder also owns this catalog and relicenses these adapted copies under this
skill's MIT `LICENSE.txt`. The catalog validator requires the downstream MIT
notice in full:

```
MIT License

Copyright (c) 2026 jointsome0-lgtm

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
