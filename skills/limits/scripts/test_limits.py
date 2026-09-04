"""Run the limits checker against fixture repositories and check each limiter fires."""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent / "limits.py"
WORKFLOW = SCRIPT.parent.parent / "templates" / "limits.yml"

README = """# fixture

## Mapping notes

A decoy section whose heading and this literal ## Map mention must not
anchor the parser.

```text
## Map
```

## Map

- `src/`: source layout root.
- `src/pkg/`: the package.
- `tests/`: goal tests.
"""

GOALS = """# fixture

Rules of this file: each numbered line names exactly one test, naïvely.

1. The package holds a value.
   `tests/test_works.py`

```
1. A fenced example that is not a goal.
```

  ~~~markdown
2. A tilde-fenced example that is not a goal either.
  ~~~
"""


class LimitsFixtureTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="limits-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / "README.md").write_text(README, encoding="utf-8")
        (self.root / "GOALS.md").write_text(GOALS, encoding="utf-8")
        (self.root / "src" / "pkg" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_works.py").write_text(
            "class TestWorks:\n    def test_works(self):\n        assert True\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.stage()

    def stage(self):
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)

    def run_limits(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_clean_fixture_passes(self):
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("limits: 0 problems", result.stdout)
        self.assertIn(f"of {70_000} tokens", result.stdout)

    @unittest.skipIf(os.name == "nt", "Win32 does not preserve trailing spaces")
    def test_repository_root_preserves_trailing_space(self):
        spaced = self.root.with_name(f"{self.root.name} ")
        self.root.rename(spaced)
        self.root = spaced
        self.addCleanup(shutil.rmtree, spaced, ignore_errors=True)
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_repository_root_preserves_non_utf8_bytes(self):
        encoded = os.fsencode(self.root) + b"-\xff"
        try:
            os.rename(os.fsencode(self.root), encoded)
        except OSError:
            self.skipTest("filesystem rejects non-UTF-8 names")
        self.root = pathlib.Path(os.fsdecode(encoded))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipIf(os.name == "nt", "Win32 does not preserve newlines")
    def test_repository_root_preserves_trailing_newline(self):
        renamed = self.root.with_name(f"{self.root.name}\n")
        self.root.rename(renamed)
        self.root = renamed
        self.addCleanup(shutil.rmtree, renamed, ignore_errors=True)
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipIf(os.name == "nt", "Win32 does not preserve carriage returns")
    def test_repository_root_preserves_trailing_carriage_return(self):
        renamed = self.root.with_name(f"{self.root.name}\r")
        self.root.rename(renamed)
        self.root = renamed
        self.addCleanup(shutil.rmtree, renamed, ignore_errors=True)
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_package_argument_prints_usage(self):
        result = self.run_limits()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stdout)

    def test_budget_argument_overrides_default(self):
        result = self.run_limits("pkg", "1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("limit 1", result.stdout)

    def test_budget_uses_staged_blob_sizes(self):
        payload = self.root / "payload.txt"
        payload.write_text("small\n", encoding="utf-8")
        self.stage()
        baseline = self.run_limits("pkg")
        match = re.search(r"budget: (\d+) of", baseline.stdout)
        self.assertIsNotNone(match)
        budget = match.group(1)
        payload.write_text("large\n" * 100_000, encoding="utf-8")
        result = self.run_limits("pkg", budget)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_python_markdown_and_import_limiters_fire(self):
        (self.root / "src" / "pkg" / "extra.py").write_text(
            '"""module doc"""\nX = 1  # explains itself\n', encoding="utf-8"
        )
        (self.root / "NOTES.md").write_text("scratch\n", encoding="utf-8")
        (self.root / "tests" / "test_works.py").write_text(
            "import pkg\nimport pkg.testing\nimport pkg.testing as ok\nfrom pkg.testing import fake\n\ndef test_works():\n    assert fake\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        for needle in (
            "comment:",
            "docstring:",
            "artifact: 'NOTES.md'",
            "test import:",
        ):
            self.assertIn(needle, result.stdout)
        self.assertEqual(result.stdout.count("test import:"), 2)
        self.assertNotIn("pkg.testing", result.stdout)
        self.assertNotIn("goals:", result.stdout)

    def test_import_without_fromlist_exposes_package_root(self):
        (self.root / "tests" / "test_works.py").write_text(
            'pkg = __import__("pkg.testing")\n'
            'allowed = __import__("pkg.testing", fromlist=["testing"])\n\n'
            "def test_works():\n"
            "    assert pkg and allowed\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count("test import:"), 1)
        self.assertIn("test import: 'tests/test_works.py':1 'pkg'", result.stdout)

    def test_import_with_computed_empty_fromlist_exposes_package_root(self):
        (self.root / "tests" / "test_works.py").write_text(
            "parts = []\n"
            'pkg = __import__("pkg.testing", fromlist=parts)\n\n'
            "def test_works():\n"
            "    assert pkg\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count("test import:"), 1)
        self.assertIn("test import: 'tests/test_works.py':2 'pkg'", result.stdout)

    def test_dynamic_loader_aliases_are_import_checked(self):
        (self.root / "tests" / "test_works.py").write_text(
            "from importlib import import_module as load\n"
            "from pytest import importorskip as skip\n\n"
            'first = load("pkg.internal")\n'
            'second = skip("pkg.internal")\n\n'
            "def test_works():\n"
            "    assert first and second\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count("test import:"), 2)

    def test_helper_under_tests_is_import_checked(self):
        (self.root / "tests" / "helper.py").write_text(
            "import pkg.internal\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("test import: 'tests/helper.py':1 'pkg'", result.stdout)

    def test_package_relative_static_import_is_rejected(self):
        package_tests = self.root / "src" / "pkg" / "tests"
        package_tests.mkdir()
        (package_tests / "test_inside.py").write_text(
            "from .. import internal\n\ndef test_inside():\n    assert internal\n",
            encoding="utf-8",
        )
        (self.root / "README.md").write_text(
            README.rstrip() + "\n- `src/pkg/tests/`: package tests.\n",
            encoding="utf-8",
        )
        (self.root / "GOALS.md").write_text(
            GOALS + "\n2. Package tests stay behind the public API.\n"
            "   `src/pkg/tests/test_inside.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "test import: 'src/pkg/tests/test_inside.py':1 'pkg'", result.stdout
        )
        self.assertNotIn("goals:", result.stdout)

    def test_bare_imports_reject_dotted_package_root(self):
        (self.root / "tests" / "test_works.py").write_text(
            "import pkg.sub.testing\n"
            "import pkg.sub.testing as allowed\n"
            'dynamic = __import__("pkg.sub.testing")\n'
            'allowed_dynamic = __import__("pkg.sub.testing", fromlist=["testing"])\n\n'
            "def test_works():\n"
            "    assert allowed and dynamic and allowed_dynamic\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg.sub")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count("test import:"), 2)
        self.assertIn("'pkg.sub'", result.stdout)

    def test_relative_import_module_resolves_allowed_api(self):
        (self.root / "tests" / "test_works.py").write_text(
            "import importlib\n\n"
            'testing = importlib.import_module(".testing", "pkg")\n\n'
            "def test_works():\n"
            "    assert testing\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_map_heading_fires(self):
        (self.root / "README.md").write_text("# fixture\n", encoding="utf-8")
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("map: no ## Map heading in README.md", result.stdout)

    def test_malformed_first_map_item_fires_without_visible_directories(self):
        shutil.rmtree(self.root / "src")
        shutil.rmtree(self.root / "tests")
        (self.root / "README.md").write_text(
            "# fixture\n\n## Map\n\n- malformed\n", encoding="utf-8"
        )
        (self.root / "GOALS.md").write_text("# fixture\n", encoding="utf-8")
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("map: wrapped line", result.stdout)
        self.assertNotIn("map: no line for", result.stdout)

    def test_map_rejects_nonblank_content_before_first_hyphen_item(self):
        (self.root / "README.md").write_text(
            README.replace(
                "## Map\n\n",
                "## Map\n\nMap introduction.\n* malformed\n",
            ),
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count("map: wrapped line"), 2)

    def test_html_commented_map_heading_is_ignored(self):
        (self.root / "README.md").write_text(
            "<!--\n## Map\n- malformed\n-->\n\n" + README, encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_setext_heading_ends_map_section(self):
        (self.root / "README.md").write_text(
            README + "\nOther section\n-------------\n\nProse.\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_indented_code_before_thematic_break_stays_in_map(self):
        (self.root / "README.md").write_text(
            README.rstrip() + "\n    hidden code\n---\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("map: wrapped line", result.stdout)

    def test_html_commented_goal_is_ignored(self):
        (self.root / "GOALS.md").write_text(
            GOALS + "\n<!--\n2. Hidden example.\n   `tests/test_hidden.py`\n-->\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_goal_allows_blank_line_before_test_path(self):
        (self.root / "GOALS.md").write_text(
            GOALS.replace(
                "1. The package holds a value.\n   `tests/test_works.py`",
                "1. The package holds a value.\n\n   `tests/test_works.py`",
            ),
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_goal_accepts_bare_marker_with_indented_content(self):
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n"
            "1.\n"
            "   The package holds a value.\n"
            "   `tests/test_works.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_goal_tab_indent_uses_marker_column(self):
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n"
            "1.\tThe package holds a value.\n"
            "    - Verified by `tests/test_works.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_goal_recognizes_indented_parenthesis_marker(self):
        (self.root / "tests" / "test_works.py").write_text(
            "VALUE = True\n", encoding="utf-8"
        )
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n   1) A goal without a test path.\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("goals: entry 1 names 0 tests", result.stdout)

    def test_heading_ends_goal_entry(self):
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n"
            "1. A goal without a test path.\n"
            "## Separate section\n"
            "`tests/test_works.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("goals: entry 1 names 0 tests", result.stdout)

    def test_map_goal_and_symlink_drift_fire(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "notes.txt").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_extra.py").write_text(
            "def test_extra():\n    assert True\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_link.py").write_text(
            "../missing.py", encoding="utf-8"
        )
        self.stage()
        blob = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=self.root,
            input="../missing.py",
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "update-index", "--cacheinfo", f"120000,{blob},tests/test_link.py"],
            cwd=self.root,
            check=True,
        )
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("map: no line for 'docs/'", result.stdout)
        self.assertIn(
            "goals: 'tests/test_extra.py' exists but no goal names it", result.stdout
        )
        self.assertIn("symlink: 'tests/test_link.py'", result.stdout)
        self.assertNotIn("test_link.py exists but no goal names it", result.stdout)

    def test_python_named_gitlink_is_not_read_as_source(self):
        (self.root / "README.md").write_text(
            README.rstrip() + "\n- `vendor.py/`: a pinned dependency.\n",
            encoding="utf-8",
        )
        self.stage()
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=self.root,
            check=True,
        )
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        subprocess.run(
            [
                "git",
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{commit},vendor.py",
            ],
            cwd=self.root,
            check=True,
        )
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unordered_sibling_ends_goal_entry(self):
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n"
            "1. A goal without a test path.\n"
            "- Separate item: `tests/test_works.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("goals: entry 1 names 0 tests", result.stdout)

    def test_test_definition_inside_string_does_not_count(self):
        (self.root / "tests" / "test_works.py").write_text(
            'SOURCE = """\ndef test_works():\n    pass\n"""\n', encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("test: 'tests/test_works.py' defines no test", result.stdout)

    def test_nested_test_function_does_not_count(self):
        (self.root / "tests" / "test_works.py").write_text(
            "def helper():\n"
            "    def test_hidden():\n"
            "        assert True\n"
            "    return test_hidden\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("test: 'tests/test_works.py' defines no test", result.stdout)

    def test_map_description_must_not_be_blank(self):
        (self.root / "README.md").write_text(
            README.replace("- `src/`: source layout root.", "- `src/`:    "),
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("map: wrapped line", result.stdout)

    @unittest.skipIf(os.name == "nt", "creating symlinks needs extra Windows rights")
    def test_required_symlink_is_not_read(self):
        readme = self.root / "README.md"
        readme.unlink()
        readme.symlink_to("missing-readme")
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("symlink: 'README.md'", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_required_files_are_reported(self):
        (self.root / "README.md").unlink()
        (self.root / "GOALS.md").unlink()
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("required file: 'README.md' is missing", result.stdout)
        self.assertIn("required file: 'GOALS.md' is missing", result.stdout)
        self.assertIn("limits: 2 problems", result.stdout)

    def test_nested_list_stays_inside_goal_entry(self):
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n"
            "1. The package holds a value.\n"
            "   - Verified by `tests/test_works.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_thematic_break_does_not_hide_final_map_item(self):
        (self.root / "README.md").write_text(
            README.rstrip() + "\n---\n\nAfter the Map.\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_mixed_fence_characters_do_not_close_code_block(self):
        (self.root / "GOALS.md").write_text(
            "# fixture\n\n"
            "```text\n"
            "```~~~\n"
            "1. Hidden example.\n"
            "   `tests/test_works.py`\n"
            "```\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "goals: 'tests/test_works.py' exists but no goal names it", result.stdout
        )

    def test_raw_html_blocks_do_not_create_goals(self):
        for opening, closing in (
            ("<pre>", "</pre>"),
            ("<div>", "</div>"),
            ("<fixture-card>", "</fixture-card>"),
        ):
            with self.subTest(opening=opening):
                (self.root / "GOALS.md").write_text(
                    "# fixture\n\n"
                    f"{opening}\n"
                    "1. Hidden example.\n"
                    "   `tests/test_works.py`\n"
                    f"{closing}\n",
                    encoding="utf-8",
                )
                self.stage()
                result = self.run_limits("pkg")
                self.assertEqual(result.returncode, 1)
                self.assertIn(
                    "goals: 'tests/test_works.py' exists but no goal names it",
                    result.stdout,
                )

    def test_root_test_is_bound_and_import_checked(self):
        (self.root / "test_root.py").write_text(
            "import pkg\n\ndef test_root():\n    assert pkg\n", encoding="utf-8"
        )
        (self.root / "GOALS.md").write_text(
            GOALS + "\n2. The root test stays bound.\n   `test_root.py`\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("test import: 'test_root.py':1 'pkg'", result.stdout)
        self.assertNotIn("goals:", result.stdout)

    def test_test_module_in_other_directory_requires_goal(self):
        (self.root / "integration").mkdir()
        (self.root / "integration" / "test_api.py").write_text(
            "def test_api():\n    assert True\n", encoding="utf-8"
        )
        (self.root / "README.md").write_text(
            README.rstrip() + "\n- `integration/`: integration tests.\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "goals: 'integration/test_api.py' exists but no goal names it",
            result.stdout,
        )

    def test_utf8_bom_python_source_is_read_by_interpreter_rules(self):
        (self.root / "src" / "pkg" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8-sig"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_test_module_is_bound_and_rejected(self):
        (self.root / "tests" / "test_placeholder.py").write_text(
            "VALUE = True\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "test: 'tests/test_placeholder.py' defines no test", result.stdout
        )
        self.assertIn(
            "goals: 'tests/test_placeholder.py' exists but no goal names it",
            result.stdout,
        )

    def test_control_characters_in_paths_are_escaped(self):
        name = "forged\n::error title=forged::message.md"
        (self.root / name).write_text("scratch\n", encoding="utf-8")
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("\n::error title=forged::message.md", result.stdout)
        self.assertIn("\\n::error title=forged::message.md", result.stdout)

    def test_workflow_restricts_repository_token(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read\n", text)


if __name__ == "__main__":
    unittest.main()
