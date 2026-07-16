#!/usr/bin/env python3
"""Self-test for check_version_bump.py against invented fixture repositories."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_version_bump.py"

GIT_ENV_FLAGS = [
    "-c", "user.name=Fixture",
    "-c", "user.email=fixture@example.invalid",
    "-c", "commit.gpgsign=false",
]


class CheckVersionBumpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="version-bump-test."))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.git("init", "--quiet", "--initial-branch=main")
        self.write_plugin("demo", "1.0.0")
        (self.repo / "README.md").write_text("Invented fixture repository.\n", encoding="utf-8")
        self.commit("initial layout")

    def git(self, *argv: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *GIT_ENV_FLAGS, *argv], capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(result.returncode, 0, f"git {argv}: {result.stderr}")
        return result

    def commit(self, message: str) -> None:
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)

    def write_plugin(self, name: str, version: str) -> None:
        manifest = self.repo / "plugins" / name / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps({"name": name, "version": version, "description": "Invented plugin."})
            + "\n",
            encoding="utf-8",
        )
        skill = self.repo / "plugins" / name / "skills" / name / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(f"# {name}\n\nInvented skill body.\n", encoding="utf-8")

    def touch_skill(self, name: str, line: str) -> None:
        skill = self.repo / "plugins" / name / "skills" / name / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + line + "\n", encoding="utf-8")

    def check(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--base", "main", *argv],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )

    def branch(self, name: str = "feature") -> None:
        self.git("checkout", "--quiet", "-b", name)

    def test_content_change_without_bump_fails(self) -> None:
        self.branch()
        self.touch_skill("demo", "Invented edit without a bump.")
        self.commit("edit demo skill")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("plugins/demo", result.stderr)
        self.assertIn("'1.0.0'", result.stderr)
        self.assertIn("bump plugins/demo/.claude-plugin/plugin.json", result.stderr)

    def test_content_change_with_bump_passes(self) -> None:
        self.branch()
        self.touch_skill("demo", "Invented edit shipped with a bump.")
        self.write_plugin("demo", "1.0.1")
        self.commit("edit demo skill and bump")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 changed plugin(s)", result.stdout)

    def test_bump_only_diff_passes(self) -> None:
        self.branch()
        self.write_plugin("demo", "1.1.0")
        self.commit("bump only")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_new_plugin_passes(self) -> None:
        self.branch()
        self.write_plugin("fresh", "0.1.0")
        self.commit("add fresh plugin")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_deleted_plugin_passes(self) -> None:
        self.branch()
        shutil.rmtree(self.repo / "plugins" / "demo")
        self.commit("remove demo plugin")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_change_outside_plugins_passes(self) -> None:
        self.branch()
        (self.repo / "README.md").write_text("Invented update.\n", encoding="utf-8")
        self.commit("update readme")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no plugin content changes", result.stdout)

    def test_uncommitted_change_without_bump_fails(self) -> None:
        self.branch()
        self.touch_skill("demo", "Invented uncommitted edit.")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("plugins/demo", result.stderr)

    def test_names_only_the_unbumped_plugin(self) -> None:
        self.write_plugin("extra", "2.0.0")
        self.commit("add extra plugin")
        self.branch()
        self.touch_skill("demo", "Invented bumped edit.")
        self.write_plugin("demo", "1.0.1")
        self.touch_skill("extra", "Invented unbumped edit.")
        self.commit("edit both, bump one")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("plugins/extra", result.stderr)
        self.assertNotIn("plugins/demo:", result.stderr)

    def test_unresolvable_base_is_reported(self) -> None:
        result = self.check("--base", "no-such-ref")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not resolve", result.stderr)

    def test_invalid_head_manifest_is_reported(self) -> None:
        self.branch()
        manifest = self.repo / "plugins" / "demo" / ".claude-plugin" / "plugin.json"
        manifest.write_text("{not json", encoding="utf-8")
        self.commit("break manifest")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("invalid JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
