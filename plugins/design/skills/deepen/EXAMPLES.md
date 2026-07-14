# Worked examples

Invented fixtures — an imaginary repository `driftline` with an SDD, a Decision Log, and an importer subsystem. Nothing here refers to a real project.

## 1. Named scope: scan only what was named

> "Deepen the importer — adding a new source format keeps taking a week."

The user named a subsystem and a pain point, so scoping inference is skipped. The run reads `AGENTS.md`, the SDD map, only the importer §§ (`§4 Import pipeline`, `§7 Source adapters`), the two Decision Log entries touching importers, and one open importer issue — then explores `importer/` code, its tests, and its slice of history. The exporter, API, and UI are never read; the report's header states the scope as "importer subsystem (user-named)". Candidates outside the importer do not appear, even if the explore pass happened to smell them from call sites.

## 2. No scope named: bounded hot spots, not a repo-wide review

> "Anything worth deepening in driftline?"

No direction named, so the run walks `git log --oneline -100` and tallies the areas that keep coming up: `importer/normalize/` (31 commits) and `billing/rates.py` (14 commits) dominate; nothing else clears noise. The scan covers those two hot spots only. The report says so: "Scope: last 100 commits → 2 hot spots; the other 12 top-level modules were not reviewed." Widening would need evidence — scattered changes with no hot spot, or a symptom crossing a wider seam — and neither is present, so a full-repository review is explicitly *not* run.

## 3. Evidence-grounded candidate, not a line-count smell

The explore pass finds `importer/normalize/trim.py` — 14 lines, one function. Short is not a finding. The candidate that ships is grounded in traced friction: fixing "dates parse wrong for the EU feed" required touching `fetch.py → decode.py → trim.py → dates.py → emit.py` (call path traced), the five files changed together in 9 of the last 12 importer commits (change locality from the scoped history), and the bug's regression test could only be written end-to-end because no interface exposes normalization as one step (test surface). Card: *"Normalization is five shallow modules — one concept, five hops. Evidence: call trace fetch→emit; 9/12 commits co-change; no unit-testable seam. Deepen: one `normalize(feed) → Records` interface. Strong."* The deletion test confirms: deleting the five wrappers concentrates complexity into one module rather than moving it.

## 4. A recorded decision is respected — until real new evidence

Driftline's Decision Log has: `- 2042-03-10 — importer fetch/parse stay separate modules; retry policy differs per source`. A run whose evidence is merely "fetch and parse look mergeable" suppresses that candidate — recorded decision, no new friction, nothing to show. A later run has concrete new evidence: three of the month's five importer fixes each straddled the fetch/parse seam, and the per-source retry policies have since converged to one. The candidate now appears, with the callout: *"Conflicts with Decision Log 2042-03-10 (fetch/parse separate) — worth reopening: retry policies converged; 3/5 recent fixes crossed the seam."* Reopening remains the owner's call in the grilling loop; the card only makes the case.

## 5. Non-interactive run: report and drafts, nothing durable

A scheduled, unattended run produces the report at `$TMPDIR/architecture-review-<timestamp>.html` and prints its path plus draft decision material into the session log. It creates no GitHub issue, no Decision Log line, no SDD edit, and no code change, and commits nothing — the repository is byte-identical afterwards. The owner reads the report later and, in a live session, picks a candidate; only that live selection starts step 3.

## 6. Selected candidate → three interfaces, one recommendation

The owner picks the normalization candidate. The grilling loop establishes constraints (streaming feeds must not buffer fully; per-source quirks stay behind the seam) and dependency category (`local-substitutable` — a fake feed file substitutes in tests). Genuinely different interfaces would improve the decision, so design-it-twice runs three independent passes: **Design 1** minimal — `normalize(feed) → Iterator[Record]`, one entry point; **Design 2** flexible — a `Normalizer` with pluggable per-source stages; **Design 3** caller-first — `records(source_id)` that hides fetch *and* normalize behind one call. The comparison recommends Design 1 (highest leverage per entry point; Design 3 moves the fetch seam without evidence). Owner accepts. The confirmed payload — a focused issue titled "Deepen importer normalization behind `normalize(feed)`", written in the skill's own words with SDD § citations — is shown verbatim, confirmed, and only then created. The report file stays in the temp directory; nothing else durable exists.
