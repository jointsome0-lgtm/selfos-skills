"""Run the limits checker against fixture repositories and check each limiter fires."""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent / "limits.py"

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
        for needle in ("comment:", "docstring:", "artifact: NOTES.md", "test import:"):
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
        self.assertIn("test import: tests/test_works.py:1 pkg", result.stdout)

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

    def test_html_commented_map_heading_is_ignored(self):
        (self.root / "README.md").write_text(
            "<!--\n## Map\n- malformed\n-->\n\n" + README, encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
        self.assertIn("map: no line for docs/", result.stdout)
        self.assertIn(
            "goals: tests/test_extra.py exists but no goal names it", result.stdout
        )
        self.assertIn("symlink: tests/test_link.py", result.stdout)
        self.assertNotIn("test_link.py exists but no goal names it", result.stdout)


if __name__ == "__main__":
    unittest.main()
