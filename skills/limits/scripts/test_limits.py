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

This mention of ## Map is not a heading.

```text
## Map
- malformed example
```

## Map

- `src/`: source layout root.
- `src/pkg/`: the package.
- `tests/`: goal tests.
"""
GOALS = """# fixture

1. The package holds a value.
   `tests/test_works.py`

~~~text
2. A fenced example without a test.
~~~
"""
TEST = "def test_works():\n    assert True\n"


class LimitsFixtureTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="limits-fixture-"))
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))
        self.write("README.md", README)
        self.write("GOALS.md", GOALS)
        self.write("src/pkg/__init__.py", "VALUE = 1\n")
        self.write("tests/test_works.py", TEST)
        self.git("init", "-q")

    def write(self, path, text, encoding="utf-8"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding=encoding)

    def git(self, *args, **kwargs):
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        ).stdout.strip()

    def check(self, *needles, package="pkg", budget=None, stage=True, code=None):
        if stage:
            self.git("add", "-A")
        args = [] if package is None else [package]
        if budget is not None:
            args.append(str(budget))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        expected = code if code is not None else int(bool(needles))
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stdout)
        return result.stdout

    def test_cli_and_budget(self):
        self.assertIn("of 70000 tokens", self.check())
        self.check("usage:", package=None, code=2)
        self.check("limit 1", budget=1)

    def test_budget_counts_staged_blobs(self):
        self.write("payload.txt", "small\n")
        budget = re.search(r"budget: (\d+) of", self.check())[1]
        self.write("payload.txt", "large\n" * 100_000)
        self.check(budget=budget, stage=False)

    def test_python_and_markdown_rules(self):
        self.write("src/pkg/extra.py", '"""module doc"""\nX = 1  # prose\n')
        self.write("NOTES.md", "scratch\n")
        self.check("comment:", "docstring:", "artifact: 'NOTES.md'")

    def test_machine_markers_and_source_encoding(self):
        self.write("src/pkg/__init__.py", "VALUE = 1\n", encoding="utf-8-sig")
        self.write(
            "src/pkg/markers.py",
            "#!/usr/bin/env python3\nX = 1  # noqa\nY = X  # type: ignore\n",
        )
        self.check()

    def test_static_imports(self):
        cases = (
            ("import pkg", 1),
            ("import pkg.testing", 1),
            ("import pkg.testing as testing", 0),
            ("from pkg.testing import fake", 0),
            ("from pkg import testing", 1),
            ("import pkg.internal as internal", 1),
            ("import unrelated", 0),
        )
        for source, count in cases:
            with self.subTest(source=source):
                self.write("tests/test_works.py", source + "\n" + TEST)
                output = self.check(code=int(bool(count)))
                self.assertEqual(output.count("test import:"), count, output)

    def test_dynamic_imports(self):
        cases = (
            ('__import__("pkg.testing")', 1),
            ('__import__("pkg.testing", fromlist=["fake"])', 0),
            ('__import__("pkg.testing", fromlist=parts)', 1),
            ('__import__("pkg.testing", fromlist=[*()])', 1),
            ('__import__("pkg.testing", fromlist={**{}})', 1),
            ('__import__("pkg.testing", fromlist=[part])', 1),
            ('__import__("pkg.testing", fromlist=("fake",))', 0),
            ('__import__("internal", globals(), locals(), ["x"], 2)', 1),
            ('__import__("internal", level=level)', 1),
            ('__import__("pkg.testing", fromlist=["fake"], level=0)', 0),
            ('import importlib\nimportlib.import_module("pkg.internal")', 1),
            ('import importlib as loader\nloader.import_module(name="pkg.testing")', 0),
            ('from importlib import import_module as load\nload("pkg.internal")', 1),
            ('from importlib import *\nimport_module("pkg.internal")', 1),
            ('from pytest import *\nimportorskip("pkg.internal")', 1),
            ('import importlib\nimportlib.import_module("pkg.internal-name")', 1),
            ('from builtins import __import__ as load\nload("pkg.testing")', 1),
            ('from importlib import __import__ as load\nload("pkg.internal")', 1),
            ('import importlib\nimportlib.__import__("pkg.internal")', 1),
            (
                'from importlib import __import__ as load\nload("pkg.testing", fromlist=["fake"])',
                0,
            ),
            ('import pytest as p\np.importorskip("pkg.internal")', 1),
            ('from pytest import importorskip as skip\nskip(modname="pkg.testing")', 0),
            ("import importlib\nimportlib.import_module(target)", 1),
            ('import importlib\nimportlib.import_module(".testing", "pkg")', 0),
            ('import importlib\nimportlib.import_module(".internal", "pkg")', 1),
            ('import importlib\nimportlib.import_module(".testing", package)', 1),
            ('loader.import_module("pkg.internal")', 0),
        )
        for source, count in cases:
            with self.subTest(source=source):
                self.write("tests/test_works.py", source + "\n" + TEST)
                output = self.check(code=int(bool(count)))
                self.assertEqual(output.count("test import:"), count, output)

    def test_loader_aliases_are_file_wide_and_require_direct_calls(self):
        self.write(
            "tests/test_works.py",
            "from importlib import import_module as load\n"
            "def test_works():\n    def load(name):\n        return name\n"
            '    assert load("pkg.internal")\n',
        )
        self.check("test import:")
        for source in (
            "import importlib\nload = importlib.import_module",
            "from importlib import import_module as load\nconsume(load)",
        ):
            with self.subTest(source=source):
                self.write("tests/test_works.py", source + "\n" + TEST)
                self.check("test loader reference: 'tests/test_works.py':2")

    def test_dotted_package_imports(self):
        cases = (
            ("import pkg.sub.testing", 1),
            ("import pkg.sub.testing as allowed", 0),
            ('__import__("pkg.sub.testing")', 1),
            ('__import__("pkg.sub.testing", fromlist=["fake"])', 0),
            ("from pkg import sub", 1),
            ("from pkg import sub as protected", 1),
            ("from pkg import *", 1),
            ("from pkg import unrelated", 0),
            ("from pkg.sub.testing import fake", 0),
        )
        for source, count in cases:
            with self.subTest(source=source):
                self.write("tests/test_works.py", source + "\n" + TEST)
                output = self.check(package="pkg.sub", code=int(bool(count)))
                self.assertEqual(output.count("test import:"), count, output)

    def test_pytest_plugins(self):
        for value, bad in (
            ("'pkg.testing'", False),
            ("'helper,pkg.internal'", True),
            ("'helper,pkg.testing'", False),
            ("['pkg.internal']", True),
            ("plugins", True),
            ("[]\npytest_plugins += ['pkg.internal']", True),
        ):
            with self.subTest(value=value):
                self.write("conftest.py", f"pytest_plugins = {value}\n")
                output = self.check(code=int(bad))
                self.assertEqual(output.count("test import:"), int(bad), output)
        self.write("conftest.py", "pytest_plugins: list[str]\n")
        self.check()
        self.write("conftest.py", "pytest_plugins, unused = ['pkg.internal'], None\n")
        self.check("test import:")

    def test_test_file_scope(self):
        for path in (
            "tests/helper.py",
            "conftest.py",
            "test_root.py",
            "integration/api_test.py",
        ):
            with self.subTest(path=path):
                self.write(path, "import pkg.internal\n" + TEST)
                output = self.check(f"test import: {path!a}:1")
                if path in ("test_root.py", "integration/api_test.py"):
                    self.assertIn(
                        f"goals: {path!a} exists but no goal names it", output
                    )
                (self.root / path).unlink()

    def test_package_relative_import(self):
        path = "src/pkg/tests/test_inside.py"
        self.write(path, "from .. import internal\n" + TEST)
        self.write("README.md", README + "- `src/pkg/tests/`: package tests.\n")
        self.write("GOALS.md", GOALS + f"\n2. Internal tests use the seam. `{path}`\n")
        output = self.check(f"test import: {path!a}:1 'pkg'")
        self.assertNotIn("goals:", output)
        (self.root / "src").rename(self.root / "lib")
        for name in ("README.md", "GOALS.md"):
            self.write(name, (self.root / name).read_text().replace("`src/", "`lib/"))
        self.check("test import: 'lib/pkg/tests/test_inside.py':1 'pkg'")

    def test_map_grammar(self):
        cases = (
            ("# fixture\n", "map: no ## Map heading"),
            (
                README.replace("- `src/`: source layout root.", "- malformed"),
                "map: wrapped line",
            ),
            (
                README.replace("- `src/`: source layout root.", "- `src/`:    "),
                "map: wrapped line",
            ),
            (
                README.replace("## Map\n\n", "## Map\n\nIntroduction.\n"),
                "map: wrapped line",
            ),
            (README + "  continued description\n", "map: wrapped line"),
            (README + "- `src/`: duplicate.\n", "map: duplicate line for 'src/'"),
            (
                README + "- `absent/`: missing directory.\n",
                "map: no directory 'absent/'",
            ),
            (README.replace("source layout root.", "x" * 250), "exceeds 250 chars"),
        )
        for text, error in cases:
            with self.subTest(error=error, text=text):
                self.write("README.md", text)
                self.check(error)

    def test_markdown_examples_and_next_heading(self):
        self.write(
            "README.md",
            "<!--\n## Map\n- malformed\n-->\n" + README + "\n## Other\nProse.\n",
        )
        self.write("GOALS.md", GOALS + "\n<!--\n2. Hidden goal without a test.\n-->\n")
        self.check()
        self.write("GOALS.md", "Intro `<!--`\n\n1. Missing a test.\n")
        (self.root / "tests/test_works.py").unlink()
        self.write("tests/helper.py", "VALUE = 1\n")
        self.check("goals: entry 1 names 0 tests")

    def test_map_tracks_visible_directories(self):
        self.write("docs/notes.txt", "notes\n")
        self.check("map: no line for 'docs/'")
        shutil.rmtree(self.root / "docs")
        self.write(".cache/notes.txt", "cache\n")
        self.check()

    def test_goals_bind_exactly_one_existing_test(self):
        cases = (
            ("1. Missing path.\n", "goals: entry 1 names 0 tests"),
            (
                "1.    \n   `tests/test_works.py`\n",
                "goals: 'tests/test_works.py' exists but no goal names it",
            ),
            (
                "1. Two paths `tests/test_works.py` and `tests/test_other.py`.\n",
                "goals: entry 1 names 2 tests",
            ),
            (
                "1. Missing file `tests/test_missing.py`.\n",
                "goals: 'tests/test_missing.py' named in GOALS.md but missing",
            ),
            (
                "1. First `tests/test_works.py`.\n2. Second `tests/test_works.py`.\n",
                "goals: 'tests/test_works.py' named twice",
            ),
            (
                "1. No path before the blank.\n\n   `tests/test_works.py`\n",
                "goals: entry 1 names 0 tests",
            ),
            (
                "1. No path before the blank.\n   \n   `tests/test_works.py`\n",
                "goals: entry 1 names 0 tests",
            ),
            (
                "1. No path before the heading.\n## Other\n`tests/test_works.py`\n",
                "goals: entry 1 names 0 tests",
            ),
            (
                "1. No path before prose.\nSeparate `tests/test_works.py`.\n",
                "goals: entry 1 names 0 tests",
            ),
        )
        for text, error in cases:
            with self.subTest(text=text):
                self.write("GOALS.md", text)
                self.check(error)

    def test_definition_syntax(self):
        cases = (
            (TEST, True),
            ("async def test_works():\n    pass\n", True),
            ("class Works:\n    def test_works(self):\n        pass\n", True),
            ("__test__ = False\n" + TEST, True),
            ("VALUE = True\n", False),
            ('SOURCE = "def test_hidden(): pass"\n', False),
            ("def helper():\n    def test_hidden():\n        pass\n", False),
        )
        for source, valid in cases:
            with self.subTest(source=source):
                self.write("tests/test_works.py", source)
                output = self.check(code=int(not valid))
                self.assertEqual("defines no test" in output, not valid, output)

    def test_definition_and_goal_checks_are_independent(self):
        self.write("tests/test_placeholder.py", "VALUE = True\n")
        self.check(
            "test: 'tests/test_placeholder.py' defines no test",
            "goals: 'tests/test_placeholder.py' exists but no goal names it",
        )

    def test_pytest_configuration_does_not_change_filename_rule(self):
        self.write("pytest.ini", "[pytest]\npython_files = check_*.py\n")
        self.write("check_optional.py", TEST)
        self.check()

    def test_missing_required_inputs(self):
        for path in ("README.md", "GOALS.md"):
            (self.root / path).unlink()
        self.check(
            "required file: 'README.md' is missing",
            "required file: 'GOALS.md' is missing",
            "limits: 2 problems",
        )

    def test_index_symlink_is_rejected_without_reading_source(self):
        self.write("tests/test_link.py", "not valid Python!\n")
        self.git("add", "-A")
        blob = self.git("hash-object", "-w", "--stdin", input="../missing.py")
        self.git("update-index", "--cacheinfo", f"120000,{blob},tests/test_link.py")
        output = self.check("symlink: 'tests/test_link.py'", stage=False)
        self.assertNotIn("goals:", output)

    @unittest.skipIf(os.name == "nt", "symlinks need extra Windows rights")
    def test_required_symlink_is_not_read(self):
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to("missing-readme")
        self.check("symlink: 'README.md'")

    def test_python_named_submodule_is_not_read(self):
        self.write("README.md", README + "- `vendor.py/`: pinned dependency.\n")
        self.git("add", "-A")
        self.git(
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )
        commit = self.git("rev-parse", "HEAD")
        self.git("update-index", "--add", "--cacheinfo", f"160000,{commit},vendor.py")
        self.check(stage=False)

    @unittest.skipIf(os.name == "nt", "requires POSIX filename support")
    def test_repository_root_preserves_unusual_names(self):
        for suffix in (" ", "\n", "\r", os.fsdecode(b"-\xff")):
            with self.subTest(suffix=repr(suffix)):
                target = self.root.with_name(self.root.name + suffix)
                try:
                    self.root.rename(target)
                except OSError:
                    self.skipTest("filesystem rejects the fixture name")
                self.root = target
                self.check()

    @unittest.skipIf(os.name == "nt", "requires POSIX filename support")
    def test_diagnostic_paths_are_escaped(self):
        name = "forged\n::error title=forged::message.md"
        self.write(name, "scratch\n")
        output = self.check("artifact: " + ascii(name))
        self.assertNotIn("\n::error title=forged::message.md", output)

    def test_workflow_restricts_repository_token(self):
        self.assertIn(
            "permissions:\n  contents: read\n", WORKFLOW.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
