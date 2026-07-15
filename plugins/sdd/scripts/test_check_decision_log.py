#!/usr/bin/env python3
"""Subprocess tests for the standalone Decision Log checker."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().with_name("check_decision_log.py")

VALID_NOTES_EXAMPLES = """\
- 2042-03-12 — Adopt stable IDs for Lantern exports. Rejected: positional IDs — insertions would renumber records. #412
- 2042-04-03 — Keep Orchid builds offline. Rejected remote schema lookup because it would make CI depend on network access. GH-87
- 2042-05-21 — Record the Kestrel format version in each artifact.
  Rejected: inference from field shape — explicit versions make migrations reviewable. PR #93
"""

INVALID_NOTES_EXAMPLES = """\
- 2042-06-01 - Adopt named channels for Juniper jobs. Rejected: numbered channels — names expose intent. #501
- 2042-02-30 — Keep one catalog for Marigold packages. Rejected: per-team catalogs — one catalog avoids drift. #502
- 2042-06-03 — Store Nimbus reports beside their inputs. #503
"""


def invented_entry(extra_words: int, reference: str = "#640") -> str:
    details = " ".join(["detail"] * extra_words)
    prefix = f"{details} " if details else ""
    return (
        "- 2042-07-01 — "
        f"{prefix}Index the archive. Rejected: scattered notes — one index stays navigable. {reference}\n"
    )


class DecisionLogCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_fixture(self, name: str, content: str) -> Path:
        path = self.temp / name
        path.write_text(content, encoding="utf-8")
        return path

    def run_checker(self, *arguments: object) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(CHECKER), *(str(argument) for argument in arguments)],
            cwd=self.temp,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.stdout, "", "the checker must keep stdout empty")
        return result

    def assert_clean(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_notes_valid_and_invalid_examples(self) -> None:
        notes = (CHECKER.parents[1] / "conventions" / "DECISION-LOG.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("```markdown\n" + VALID_NOTES_EXAMPLES + "```", notes)
        self.assertIn("```markdown\n" + INVALID_NOTES_EXAMPLES + "```", notes)
        valid = self.write_fixture("notes-valid.md", VALID_NOTES_EXAMPLES)
        invalid = self.write_fixture("notes-invalid.md", INVALID_NOTES_EXAMPLES)

        self.assert_clean(self.run_checker(valid))
        failed = self.run_checker(invalid)
        self.assertEqual(failed.returncode, 1)
        self.assertIn("entry does not begin", failed.stderr)
        self.assertIn("calendar-invalid date", failed.stderr)
        self.assertIn("missing explicit rejected-alternative", failed.stderr)

    def test_entry_prefix_accepts_em_dash_and_rejects_ascii_separators(self) -> None:
        valid = self.write_fixture("prefix-valid.md", VALID_NOTES_EXAMPLES.splitlines()[0] + "\n")
        self.assert_clean(self.run_checker(valid))

        for separator in ("-", "--"):
            with self.subTest(separator=separator):
                invalid = self.write_fixture(
                    f"prefix-{len(separator)}.md",
                    "- 2042-07-02 "
                    f"{separator} Choose Cedar labels. Rejected: numeric labels — names are stable. #601\n",
                )
                result = self.run_checker(invalid)
                self.assertEqual(result.returncode, 1)
                self.assertIn("entry does not begin with '- YYYY-MM-DD — '", result.stderr)

    def test_calendar_date_has_passing_and_failing_fixtures(self) -> None:
        valid = self.write_fixture(
            "date-valid.md",
            "- 2044-02-29 — Keep Alder snapshots. Rejected: live reconstruction — snapshots preserve evidence. #602\n",
        )
        invalid = self.write_fixture(
            "date-invalid.md",
            "- 2043-02-29 — Keep Birch snapshots. Rejected: live reconstruction — snapshots preserve evidence. #603\n",
        )

        self.assert_clean(self.run_checker(valid))
        result = self.run_checker(invalid)
        self.assertEqual(result.returncode, 1)
        self.assertIn("calendar-invalid date '2043-02-29'", result.stderr)

    def test_empty_text_has_passing_and_failing_fixtures(self) -> None:
        valid = self.write_fixture(
            "text-valid.md",
            "- 2042-07-03 — Pin Elm bundle names. Rejected: generated names — pins keep reviews stable. #604\n",
        )
        invalid = self.write_fixture(
            "text-empty.md",
            "- 2042-07-03 — <!-- fixture note -->\n",
        )
        continuation_only = self.write_fixture(
            "text-continuation-only.md",
            "- 2042-07-03 — \n"
            "  Pin Elm bundle names. Rejected: generated names — pins keep reviews stable. #604\n",
        )

        self.assert_clean(self.run_checker(valid))
        result = self.run_checker(invalid)
        self.assertEqual(result.returncode, 1)
        self.assertIn("empty decision text", result.stderr)

        shifted = self.run_checker(continuation_only)
        self.assertEqual(shifted.returncode, 1)
        self.assertIn("empty decision text on the dated entry line", shifted.stderr)

    def test_rejected_clause_forms_and_missing_components(self) -> None:
        valid = self.write_fixture(
            "rejected-valid.md",
            "- 2042-07-04 — Use Fir manifests. Rejected: implicit discovery — manifests expose scope. #605\n"
            "- 2042-07-05 — Keep Grove exports local.\n"
            "  Rejected hosted assembly because schema v1.2 remains reproducible. GH-606\n",
        )
        self.assert_clean(self.run_checker(valid))

        invalid_cases = {
            "missing": "- 2042-07-06 — Use Hazel manifests for every bundle. #607\n",
            "empty-alternative": "- 2042-07-06 — Use Hazel manifests. Rejected:  — scope must be visible. #607\n",
            "empty-reason": "- 2042-07-06 — Use Hazel manifests. Rejected: discovery — . #607\n",
            "no-period": "- 2042-07-06 — Use Hazel manifests. Rejected discovery because it hides scope #607\n",
        }
        for name, content in invalid_cases.items():
            with self.subTest(name=name):
                path = self.write_fixture(f"rejected-{name}.md", content)
                result = self.run_checker(path)
                self.assertEqual(result.returncode, 1)
                self.assertIn("missing explicit rejected-alternative-with-reason clause", result.stderr)

    def test_rejected_alternative_labels_are_exact_and_post_baseline(self) -> None:
        valid = self.write_fixture(
            "rejected-labels-valid.md",
            "- 2042-07-04 — Use Fir manifests. Rejected alternative: implicit discovery — manifests expose scope. #605\n"
            "- 2042-07-05 — Keep Grove exports local. Rejected alternatives: hosted assembly — it breaks offline builds; shared storage — it hides ownership. GH-606\n",
        )
        self.assert_clean(self.run_checker("--baseline", "2042-07-01", valid))

        invalid_labels = {
            "misspelled": "Rejected alternativez:",
            "other": "Rejected option:",
        }
        for name, label in invalid_labels.items():
            with self.subTest(name=name):
                path = self.write_fixture(
                    f"rejected-label-{name}.md",
                    f"- 2042-07-04 — Use Fir manifests. {label} implicit discovery — manifests expose scope. #605\n",
                )
                result = self.run_checker("--baseline", "2042-07-01", path)
                self.assertEqual(result.returncode, 1)
                self.assertIn(
                    "missing explicit rejected-alternative-with-reason clause",
                    result.stderr,
                )

        paragraph = self.write_fixture(
            "rejected-label-paragraph.md",
            "- 2042-07-04 — Use Fir manifests. Rejected alternative: folder scans — manifests expose scope. "
            "One tool writes them. Another reads them. Reviewers diff them. #605\n",
        )
        heuristic = self.run_checker("--baseline", "2042-07-01", paragraph)
        self.assertEqual(heuristic.returncode, 0, heuristic.stderr)
        self.assertIn("paragraph-style duplication heuristic", heuristic.stderr)

    def test_continuation_indentation_and_multi_entry_ambiguity(self) -> None:
        valid = self.write_fixture(
            "continuation-valid.md",
            "- 2042-07-07 — Keep Iris metadata beside each asset.\n"
            "  Rejected: a central metadata service — colocated files remain portable. #608\n",
        )
        self.assert_clean(self.run_checker(valid))

        invalid_lines = {
            "one-space": " Rejected: a service — files remain portable. #609",
            "three-spaces": "   Rejected: a service — files remain portable. #609",
            "tab": "\tRejected: a service — files remain portable. #609",
            "unattached": "  Rejected: a service — files remain portable. #609",
            "indented-entry": "  - 2042-07-08 — Use Jade files. Rejected: a service — files remain portable. #609",
            "indented-heading": "  ## Detail",
        }
        for name, bad_line in invalid_lines.items():
            with self.subTest(name=name):
                if name == "unattached":
                    content = bad_line + "\n"
                else:
                    content = "- 2042-07-08 — Keep Jade metadata beside each asset.\n" + bad_line + "\n"
                path = self.write_fixture(f"continuation-{name}.md", content)
                result = self.run_checker(path)
                self.assertEqual(result.returncode, 1)
                self.assertIn(
                    "malformed continuation indentation or multi-entry ambiguity",
                    result.stderr,
                )

    def test_ceiling_boundary_and_both_waiver_locations(self) -> None:
        at_ceiling = self.write_fixture("ceiling-pass.md", invented_entry(1))
        over_ceiling = self.write_fixture("ceiling-fail.md", invented_entry(2))
        first_line_waiver = self.write_fixture(
            "waiver-first.md",
            invented_entry(2).rstrip()
            + " <!-- decision-log: allow-long — generated migration inventory -->\n",
        )
        continuation_waiver = self.write_fixture(
            "waiver-continuation.md",
            invented_entry(2)
            + "  <!-- decision-log: allow-long — generated migration inventory -->\n",
        )
        options = ("--warn-words", "12", "--max-words", "13")

        passed = self.run_checker(*options, at_ceiling)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertNotIn("above the 13-word ceiling", passed.stderr)

        failed = self.run_checker(*options, over_ceiling)
        self.assertEqual(failed.returncode, 1)
        self.assertIn("above the 13-word ceiling", failed.stderr)
        self.assertIn("above the 12-word warning threshold", failed.stderr)

        for waived in (first_line_waiver, continuation_waiver):
            with self.subTest(waived=waived.name):
                result = self.run_checker(*options, waived)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("above the 13-word ceiling", result.stderr)
                self.assertIn("above the 12-word warning threshold", result.stderr)

    def test_waiver_requires_reason_and_exact_placement(self) -> None:
        valid = self.write_fixture(
            "waiver-valid.md",
            invented_entry(2).rstrip()
            + " <!-- decision-log: allow-long — generated compatibility matrix -->\n",
        )
        reasonless = self.write_fixture(
            "waiver-reasonless.md",
            invented_entry(2).rstrip() + " <!-- decision-log: allow-long —  -->\n",
        )
        misplaced = self.write_fixture(
            "waiver-misplaced.md",
            "- 2042-07-01 — <!-- decision-log: allow-long — compatibility matrix --> "
            "detail detail Rejected: scattered notes — one index keeps the archive navigable. #641\n",
        )
        unseparated = self.write_fixture(
            "waiver-unseparated.md",
            invented_entry(2).rstrip()
            + "<!-- decision-log: allow-long — generated compatibility matrix -->\n",
        )
        nested_in_comment = self.write_fixture(
            "waiver-nested.md",
            invented_entry(2).rstrip()
            + " <!-- wrapper <!-- decision-log: allow-long — generated compatibility matrix -->\n",
        )
        options = ("--warn-words", "12", "--max-words", "13")

        passed = self.run_checker(*options, valid)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertNotIn("requires a non-empty reason", passed.stderr)

        failed = self.run_checker(*options, reasonless)
        self.assertEqual(failed.returncode, 1)
        self.assertIn("allow-long waiver requires a non-empty reason", failed.stderr)

        placement = self.run_checker(*options, misplaced)
        self.assertEqual(placement.returncode, 1)
        self.assertIn("waiver must be at the end of the first line", placement.stderr)

        separation = self.run_checker(*options, unseparated)
        self.assertEqual(separation.returncode, 1)
        self.assertIn("waiver must be at the end of the first line", separation.stderr)

        nested = self.run_checker(*options, nested_in_comment)
        self.assertEqual(nested.returncode, 1)
        self.assertIn("waiver must use the exact HTML comment syntax", nested.stderr)

    def test_warning_threshold_boundary_and_message(self) -> None:
        at_threshold = self.write_fixture("warning-pass.md", invented_entry(0))
        over_threshold = self.write_fixture("warning-fail.md", invented_entry(1))
        options = ("--warn-words", "12", "--max-words", "20")

        self.assert_clean(self.run_checker(*options, at_threshold))
        result = self.run_checker(*options, over_threshold)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("above the 12-word warning threshold", result.stderr)
        self.assertIn("target is about 40 words", result.stderr)

    def test_stale_waiver_has_passing_and_failing_fixtures(self) -> None:
        without_waiver = self.write_fixture("stale-pass.md", invented_entry(0))
        stale = self.write_fixture(
            "stale-fail.md",
            invented_entry(0).rstrip()
            + " <!-- decision-log: allow-long — former generated appendix -->\n",
        )
        needed = self.write_fixture(
            "stale-needed.md",
            invented_entry(1).rstrip()
            + " <!-- decision-log: allow-long — generated appendix remains required -->\n",
        )
        options = ("--warn-words", "12", "--max-words", "20")

        self.assert_clean(self.run_checker(*options, without_waiver))
        result = self.run_checker(*options, stale)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stale allow-long waiver", result.stderr)

        nonstale = self.run_checker(*options, needed)
        self.assertEqual(nonstale.returncode, 0, nonstale.stderr)
        self.assertNotIn("stale allow-long waiver", nonstale.stderr)

    def test_reference_forms_and_placement_warning(self) -> None:
        references = (
            "#701",
            "PR #702",
            "GH-703",
            "abcdef0",
            "a" * 40,
            "[commit](https://invented.invalid/changes/abcdef0)",
        )
        for index, reference in enumerate(references):
            with self.subTest(reference=reference):
                path = self.write_fixture(
                    f"reference-pass-{index}.md", invented_entry(0, reference)
                )
                self.assert_clean(self.run_checker(path))

        missing_cases = (
            "",
            "abcdef",
            "a" * 41,
            "xabcdef0z",
            "generated_deadbeef_notes",
            "жdeadbeefя",
            "<!-- abcdef0 -->",
        )
        for index, reference in enumerate(missing_cases):
            with self.subTest(reference=reference or "none"):
                path = self.write_fixture(
                    f"reference-fail-{index}.md", invented_entry(0, reference).rstrip() + "\n"
                )
                result = self.run_checker(path)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("no issue/PR/SHA reference", result.stderr)
                self.assertIn(
                    "detailed argument belongs in the issue, the commit body, or the SDD § edit, not in the log",
                    result.stderr,
                )

    def test_paragraph_duplication_heuristic_boundary(self) -> None:
        two_sentences = self.write_fixture(
            "paragraph-pass.md",
            "- 2042-07-09 — Use Maple indexes. Rejected: folder scans — indexes are explicit. "
            "The exporter writes one. The verifier reads it. #704\n",
        )
        three_sentences = self.write_fixture(
            "paragraph-fail.md",
            "- 2042-07-09 — Use Maple indexes. Rejected: folder scans — indexes are explicit. "
            "The exporter writes one. The verifier reads it. Reviewers can diff it. #704\n",
        )

        self.assert_clean(self.run_checker(two_sentences))
        result = self.run_checker(three_sentences)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("paragraph-style duplication heuristic", result.stderr)
        self.assertIn("more than two sentences", result.stderr)

    def test_baseline_exemptions_and_retained_checks(self) -> None:
        historical = self.write_fixture("baseline-clean.md", invented_entry(20, ""))
        result = self.run_checker(
            "--baseline",
            "2042-07-01",
            "--warn-words",
            "12",
            "--max-words",
            "13",
            historical,
        )
        self.assert_clean(result)

        before = self.write_fixture(
            "baseline-before.md",
            invented_entry(20, "").replace("2042-07-01", "2042-06-30"),
        )
        self.assert_clean(
            self.run_checker(
                "--baseline", "2042-07-01", "--warn-words", "12", "--max-words", "13", before
            )
        )

        after = self.write_fixture(
            "baseline-after.md",
            invented_entry(20, "").replace("2042-07-01", "2042-07-02"),
        )
        current = self.run_checker(
            "--baseline", "2042-07-01", "--warn-words", "12", "--max-words", "13", after
        )
        self.assertEqual(current.returncode, 1)
        self.assertIn("above the 13-word ceiling", current.stderr)
        self.assertIn("no issue/PR/SHA reference", current.stderr)

        historical_stale = self.write_fixture(
            "baseline-stale.md",
            invented_entry(0, "").rstrip()
            + " <!-- decision-log: allow-long — old generated appendix -->\n",
        )
        self.assert_clean(
            self.run_checker(
                "--baseline", "2042-07-01", "--warn-words", "12", "--max-words", "13", historical_stale
            )
        )

        historical_missing_clause = self.write_fixture(
            "baseline-missing-clause.md",
            "- 2042-07-01 — Keep Oak output beside source files.\n",
        )
        self.assert_clean(
            self.run_checker("--baseline", "2042-07-01", historical_missing_clause)
        )
        unbaselined = self.run_checker(historical_missing_clause)
        self.assertEqual(unbaselined.returncode, 1)
        self.assertIn("missing explicit rejected-alternative", unbaselined.stderr)

        current_missing_clause = self.write_fixture(
            "baseline-current-missing-clause.md",
            "- 2042-07-02 — Keep Oak output beside source files. #710\n",
        )
        current_structure = self.run_checker(
            "--baseline", "2042-07-01", current_missing_clause
        )
        self.assertEqual(current_structure.returncode, 1)
        self.assertIn("missing explicit rejected-alternative", current_structure.stderr)

        historical_bad_date = self.write_fixture(
            "baseline-bad-date.md",
            "- 2042-02-30 — Keep Oak output beside source files.\n",
        )
        bad_date = self.run_checker(
            "--baseline", "2042-07-01", historical_bad_date
        )
        self.assertEqual(bad_date.returncode, 1)
        self.assertIn("calendar-invalid date '2042-02-30'", bad_date.stderr)

        historical_bad_continuation = self.write_fixture(
            "baseline-bad-continuation.md",
            "- 2042-07-01 — Keep Oak output beside source files.\n"
            " Rejected alternative: central storage — colocated files stay portable.\n",
        )
        bad_continuation = self.run_checker(
            "--baseline", "2042-07-01", historical_bad_continuation
        )
        self.assertEqual(bad_continuation.returncode, 1)
        self.assertIn("malformed continuation indentation", bad_continuation.stderr)

        historical_paragraph = self.write_fixture(
            "baseline-paragraph.md",
            "- 2042-07-01 — Use Pine indexes. Rejected: scans — indexes expose scope. "
            "One tool writes them. Another reads them. Reviewers diff them.\n",
        )
        paragraph = self.run_checker("--baseline", "2042-07-01", historical_paragraph)
        self.assertEqual(paragraph.returncode, 0, paragraph.stderr)
        self.assertIn("paragraph-style duplication heuristic", paragraph.stderr)

    def test_word_count_strips_link_targets_comments_prefix_and_indentation(self) -> None:
        at_threshold = self.write_fixture(
            "count-pass.md",
            "- 2042-07-10 — [visible words](https://invented.invalid/(nested(value)) target words)\n"
            "  Rejected: remote lookup — local data stays available. #705 <!-- hidden hidden -->\n",
        )
        over_threshold = self.write_fixture(
            "count-fail.md",
            "- 2042-07-10 — extra [visible words](https://invented.invalid/(nested(value)) target words)\n"
            "  Rejected: remote lookup — local data stays available. #705 <!-- hidden hidden -->\n",
        )
        options = ("--warn-words", "11", "--max-words", "20")

        self.assert_clean(self.run_checker(*options, at_threshold))
        result = self.run_checker(*options, over_threshold)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("entry has 12 words", result.stderr)

        non_link = self.write_fixture(
            "count-non-link.md",
            "- 2042-07-10 — literal ](hidden hidden hidden) "
            "Rejected: remote lookup — local data stays available. #705\n",
        )
        literal = self.run_checker("--warn-words", "12", "--max-words", "20", non_link)
        self.assertEqual(literal.returncode, 0, literal.stderr)
        self.assertIn("entry has 13 words", literal.stderr)

    def test_heading_discovery_and_whole_file_fallback(self) -> None:
        sectioned = self.write_fixture(
            "sectioned.md",
            "ordinary preface that is outside the log\n"
            "```md\n```not-a-close\n# Decision Log\ninvalid code example\n```\n"
            "### dEcIsIoN LoG ###\n"
            "- 2042-07-11 — Keep Quartz plans local. Rejected: remote plans — local plans remain reviewable. #706\n"
            "###\n"
            "ordinary appendix outside the log\n"
            "# DECISION LOG\n"
            "- 2042-07-12 — Name Rowan stages. Rejected numbered stages because names reveal intent. PR #707\n",
        )
        self.assert_clean(self.run_checker(sectioned))

        whole_file = self.write_fixture(
            "whole-file.md",
            "- 2042-07-13 — Pin Spruce layouts. Rejected: inferred layouts — pins make drift visible. #708\n",
        )
        self.assert_clean(self.run_checker(whole_file))

        whole_file_bad = self.write_fixture(
            "whole-file-bad.md",
            "This phrase mentions Decision Log but is not a heading.\n",
        )
        result = self.run_checker(whole_file_bad)
        self.assertEqual(result.returncode, 1)
        self.assertIn("malformed continuation indentation", result.stderr)

    def test_each_atx_heading_level_is_discovered(self) -> None:
        for level in range(1, 7):
            with self.subTest(level=level):
                marks = "#" * level
                indentation = " " * (level % 4)
                path = self.write_fixture(
                    f"heading-{level}.md",
                    "outside prose\n"
                    f"{indentation}{marks} decision LOG\n"
                    "- 2042-07-13 — Pin Sycamore layouts. Rejected: inferred layouts — pins expose drift. #709\n"
                    f"{indentation}{marks} Appendix\n"
                    "outside prose\n",
                )
                self.assert_clean(self.run_checker(path))

    def test_diagnostics_are_deterministic_and_sorted(self) -> None:
        a_file = self.write_fixture(
            "a-log.md",
            "- 2042-13-01 — Keep Tulip bundles together.\n",
        )
        b_file = self.write_fixture(
            "b-log.md",
            "\n- 2042-07-14 - Use Umber labels.\n",
        )

        first = self.run_checker(b_file, a_file)
        second = self.run_checker(b_file, a_file)
        self.assertEqual(first.returncode, 1)
        self.assertEqual(first.stderr, second.stderr)

        pattern = re.compile(r"^(ERROR|WARNING): (.*):(\d+): ")
        parsed = []
        for line in first.stderr.splitlines():
            match = pattern.match(line)
            self.assertIsNotNone(match, line)
            assert match is not None
            parsed.append(
                (
                    match.group(2),
                    int(match.group(3)),
                    0 if match.group(1) == "ERROR" else 1,
                    line,
                )
            )
        self.assertEqual(parsed, sorted(parsed))
        self.assertTrue(all(item[0] == str(a_file) for item in parsed[:-1]))
        self.assertEqual(parsed[-1][0], str(b_file))

    def test_usage_errors_exit_two(self) -> None:
        cases = (
            (),
            ("--baseline", "2042-02-30", "missing.md"),
            ("--warn-words", "0", "missing.md"),
            ("--warn-words", "10", "--max-words", "10", "missing.md"),
            ("--base", "2042-01-01", "missing.md"),
            ("--unknown-option", "missing.md"),
            ("does-not-exist.md",),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.run_checker(*arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
