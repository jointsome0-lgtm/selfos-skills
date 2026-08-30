#!/usr/bin/env python3
"""Run the limits checker against fixture repositories and check each limiter fires."""

import pathlib
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

## Map

- `src/`: source layout root.
- `src/pkg/`: the package.
- `tests/`: goal tests.
"""

GOALS = """# fixture

Rules of this file: each numbered line names exactly one test.

1. The package holds a value.
   `tests/test_works.py`
"""


class LimitsFixtureTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="limits-fixture-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / "README.md").write_text(README, encoding="utf-8")
        (self.root / "GOALS.md").write_text(GOALS, encoding="utf-8")
        (self.root / "src" / "pkg" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
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

    def test_python_markdown_and_import_limiters_fire(self):
        (self.root / "src" / "pkg" / "extra.py").write_text(
            '"""module doc"""\nX = 1  # explains itself\n', encoding="utf-8"
        )
        (self.root / "NOTES.md").write_text("scratch\n", encoding="utf-8")
        (self.root / "tests" / "test_works.py").write_text(
            "import pkg\nfrom pkg.testing import fake\n\ndef test_works():\n    assert fake\n",
            encoding="utf-8",
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        for needle in ("comment:", "docstring:", "artifact: NOTES.md", "test import:"):
            self.assertIn(needle, result.stdout)
        self.assertNotIn("pkg.testing", result.stdout)
        self.assertNotIn("goals:", result.stdout)

    def test_map_and_goal_drift_fire(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "notes.txt").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_extra.py").write_text(
            "def test_extra():\n    assert True\n", encoding="utf-8"
        )
        self.stage()
        result = self.run_limits("pkg")
        self.assertEqual(result.returncode, 1)
        self.assertIn("map: no line for docs/", result.stdout)
        self.assertIn("goals: tests/test_extra.py exists but no goal names it", result.stdout)


if __name__ == "__main__":
    unittest.main()
