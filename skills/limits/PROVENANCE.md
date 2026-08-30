# Provenance for skills/limits

The checker and the templates are adapted from the owner's storyworm
repository, where they survived their first adoption cycle. That repository
is private, so the pins below are auditable by the owner, not by the public.

## skills/limits/scripts/limits.py

| Field | Value |
| --- | --- |
| Upstream repository | `jointsome0-lgtm/storyworm` (private, same owner) |
| Upstream path | `scripts/limits.py` |
| Blob | `241bce37cebe4baa496508e983c7d02d32e967a0` |
| Commit | `d3a385021d17243eec257e7c712cd953393ced4c` |
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

## skills/limits/templates/

| Field | Value |
| --- | --- |
| Upstream repository | `jointsome0-lgtm/storyworm` (private, same owner) |
| Upstream paths | `AGENTS.md`, `GOALS.md`, `.github/workflows/limits.yml` |
| Commit | `d3a385021d17243eec257e7c712cd953393ced4c` |
| Commit (GOALS test rule) | `c75c71b41f56033d623b0087b55ddf5eef6dbe10` |
| Imported | 2026-08-30 |
| License | Apache-2.0 upstream (notice below) |
| Status | **adapted** |

The "Three sources of truth" and "Limiters" sections, the rules of
`GOALS.md`, and the workflow shape are upstream text with the project name,
package, and project-specific goals generalized to placeholders, plus one
added limiter bullet for the ruff and named-test steps that live outside
the script. Workflow action references are pinned to immutable commits at
the named releases.

## Upstream license notice

The upstream repository is licensed Apache-2.0 (its `LICENSE` at the pinned
commit) with the same copyright holder as this catalog, who relicenses the
adapted copies here under this skill's MIT `LICENSE.txt`. The catalog
validator requires the notice in full:

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
