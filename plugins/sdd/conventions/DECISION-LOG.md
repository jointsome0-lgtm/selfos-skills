# Decision Log — format and lint

A Decision Log entry is one dated decision line carrying the rejected
alternative and the reason. The lint (`../scripts/check_decision_log.py`)
checks structure and where detail belongs; it never judges whether a
decision is correct. Detailed argument belongs in the issue, the commit
body, or the SDD § edit — never in the log.

## Exact grammar

```text
ENTRY        := "- " DATE " — " TEXT [SPACE+ WAIVER]
CONTINUATION := "  " TEXT | "  " WAIVER
DATE         := a calendar-valid date written exactly as YYYY-MM-DD
WAIVER       := "<!-- decision-log: allow-long — " REASON " -->"
REJECTED     := "Rejected: " ALTERNATIVE " — " REASON "."
             | "Rejected " ALTERNATIVE " because " REASON "."
```

`SPACE` is an ASCII space; `TEXT`, `ALTERNATIVE`, and `REASON` contain
non-whitespace text. `Rejected` and the waiver are case-sensitive. The
clause may cross continuations; all other non-blank lines are malformed.
ASCII `-` or `--` cannot replace the em dash.

Valid examples (invented):

```markdown
- 2042-03-12 — Adopt stable IDs for Lantern exports. Rejected: positional IDs — insertions would renumber records. #412
- 2042-04-03 — Keep Orchid builds offline. Rejected remote schema lookup because it would make CI depend on network access. GH-87
- 2042-05-21 — Record the Kestrel format version in each artifact.
  Rejected: inference from field shape — explicit versions make migrations reviewable. PR #93
```

Invalid examples (ASCII dash; impossible date; missing rejected clause):

```markdown
- 2042-06-01 - Adopt named channels for Juniper jobs. Rejected: numbered channels — names expose intent. #501
- 2042-02-30 — Keep one catalog for Marigold packages. Rejected: per-team catalogs — one catalog avoids drift. #502
- 2042-06-03 — Store Nimbus reports beside their inputs. #503
```

## Length, references, and waivers

Word count joins an entry's lines with spaces, removes the leading prefix,
all HTML comments and inline Markdown link targets while retaining labels,
then counts whitespace-separated tokens. Above `--warn-words` (default 80)
the lint warns that the target is about 40 words; above `--max-words`
(default 140) it also errors unless waived. Length is a graduated signal by
design — a hard low cap was rejected in the shaping issue as brittle and
gameable.

A waiver is repository-owned and must be the exact comment above, at the
first-line end or alone on a continuation. Its reason is mandatory; it
removes only the ceiling error. At or below the warning threshold it is
stale; multiples or misplacement error.

References accept `#123`, `PR #123`, `GH-123`, or a bounded 7–40 character
hexadecimal SHA. A missing reference warns that detailed argument belongs in
the issue, commit body, or SDD § edit. More than two sentence endings after
the rejected clause triggers an explicitly heuristic duplication warning.

## Discovery, adoption, and vendoring

If an ATX heading (`#` through `######`) titled `Decision Log` exists
case-insensitively, all such sections are linted; otherwise the whole file
is the log. A section ends at the next heading of equal or higher level;
headings inside fenced code do not count.

`--baseline YYYY-MM-DD` keeps entries on or before that date
structure-checked but exempts their word thresholds, stale-waiver check, and
reference warning. It exists for adopting repositories with history; any
one-time compression of historical entries is a separate owner decision, not
this tool's job.

Vendor the lint the same way as the conventions tool (see `README.md` in
this folder): copy `../scripts/check_decision_log.py` into the consuming
repository, record its `CHECKER_VERSION` (currently `1.0.0`), wire it into
local CI, and update the copy only through an explicit PR. The file is
Python 3.9-compatible, stdlib-only, offline, and imports nothing from this
repository — a fresh subsystem checkout lints with no plugin installed.

CI semantics: structural errors exit 1 and fail the build; warnings print
clearly but never fail; usage problems exit 2.
