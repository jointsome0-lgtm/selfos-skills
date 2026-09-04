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

Named deviations in the shipped copy. Earlier forms are in git history:

1. Resolve the repository root with `git rev-parse --show-toplevel`. Accept
   the package and optional budget as CLI arguments, retaining the 70,000
   default. Missing package arguments print usage and exit 2.
2. Use repository-relative POSIX paths and filesystem decoding for Git
   output. Preserve unusual path bytes and trailing characters. Read
   Markdown as UTF-8 and Python through its tokenizer, including BOMs.
3. Read tracked paths, modes, and blob IDs from one Git index listing. Sum
   staged blob sizes in one batch call so checkout transformations do not
   change the budget. Exclude `npm-shrinkwrap.json` with the other lock files.
4. Report tracked symlinks without reading them. Exclude symlinks and
   submodules from source inspection. Report missing or submodule
   `README.md` and `GOALS.md` inputs before attempting their reads.
5. Find Map by its complete `## Map` heading, ending at the next top-level
   ATX heading. Check every nonblank row, including the first; descriptions
   must contain text. Strip ordinary fenced examples and HTML comments.
6. Read goals as unindented `N. text` paragraphs. Require nonblank text on
   the first line, with optional indented continuation lines. Blank lines
   end paragraphs. Strip fenced examples
   and HTML comments, and match separate backtick spans to test paths.
   The template defines the accepted format; this is not a Markdown renderer.
7. Match `test_*.py` and `*_test.py` files under all visible directories,
   including the root. Bind every such file to a goal and require a
   module-level `test*` function or a direct `test*` method in a top-level
   class. Inspect definitions through the AST. Pytest configuration,
   collection, and execution remain the workflow's responsibility.
8. Check imports in every Python file below a `tests/` directory, matching
   test files elsewhere, and `conftest.py`. Reject bare imports that expose
   the protected package root, including dotted package arguments. Reject
   relative static imports within that package conservatively.
   Match the package's path segments beneath any source root.
9. Recognize the three dynamic loaders through aliases declared in imports.
   Star imports bind the known loader names conservatively.
   Treat those aliases conservatively across the file, without resolving
   shadowing or reassignment. Require direct calls; report stored or passed
   loader references instead of following their later use.
10. Read each loader's module argument and require a string literal. Resolve
    relative `import_module` calls with literal packages. Treat `__import__`
    as exposing the root unless its `fromlist` is statically nonempty, and
    require its `level` to be omitted or literal zero.
    Check literal `pytest_plugins` declarations; computed, augmented, and
    destructured declarations fail. Match modules by their package prefix,
    including dynamically importable names that are not Python identifiers.
11. Escape paths and import names in diagnostics and count duplicate names
    with a counter. Format the copy with Ruff.

## skills/limits/templates/

| Field | Value |
| --- | --- |
| Source repository | Private, owner-controlled; locator omitted |
| Source commit | `d3a385021d17243eec257e7c712cd953393ced4c` |
| Goal-rule commit | `c75c71b41f56033d623b0087b55ddf5eef6dbe10` |
| Imported | 2026-08-30 |
| License | Apache-2.0 upstream (notice below) |
| Status | **adapted** |

The templates generalize project names and goals to placeholders, describe
the checked syntax, and separate the checker from the Ruff and named-test
steps. Workflow action references are pinned to immutable commits at the
named releases.

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
