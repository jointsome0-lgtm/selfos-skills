#!/usr/bin/env python3
"""Regression tests for the frozen legacy-plugin policy gate."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parent / "check_legacy_plugin_policy.py"
GIT = ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid"]


class LegacyPluginPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="legacy-policy-test."))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.git("init", "--quiet", "--initial-branch=main")
        self.write_package("demo", "1.0.0")
        self.commit("legacy package")

    def git(self, *args: str) -> None:
        result = subprocess.run(
            ["git", *GIT, *args], cwd=self.repo, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def commit(self, message: str) -> None:
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)

    def branch(self) -> None:
        self.git("checkout", "--quiet", "-b", "feature")

    def write_package(self, name: str, version: str) -> None:
        manifest = self.repo / "plugins" / name / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps({"name": name, "version": version, "description": "Deprecated."})
            + "\n",
            encoding="utf-8",
        )
        readme = self.repo / "plugins" / name / "README.md"
        readme.write_text("Deprecated fixture.\n", encoding="utf-8")

    def write_policy(self, earliest: str = "2026-10-20") -> None:
        path = self.repo / "plugins" / "deprecation.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "earliest_removal": earliest,
                    "packages": {"demo": {"deprecation_version": "1.0.1"}},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def check(self, labels: list[str] | None = None, today: str = "2026-07-20") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--base",
                "main",
                "--labels-json",
                json.dumps(labels or []),
                "--today",
                today,
            ],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

    def adopt_policy_on_main(self) -> None:
        self.write_policy()
        self.write_package("demo", "1.0.1")
        self.commit("adopt deprecation policy")

    def test_adoption_requires_every_package_notice(self) -> None:
        self.branch()
        self.write_policy()
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("must ship every package notice", result.stderr)

    def test_complete_adoption_passes_without_label(self) -> None:
        self.branch()
        self.write_policy()
        self.write_package("demo", "1.0.1")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("adopted the frozen legacy policy", result.stdout)

    def test_payload_change_without_label_fails(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        readme = self.repo / "plugins" / "demo" / "README.md"
        readme.write_text("Changed fixture.\n", encoding="utf-8")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("require exactly one", result.stderr)

    def test_compatibility_label_requires_manifest_bump_path(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        readme = self.repo / "plugins" / "demo" / "README.md"
        readme.write_text("Compatibility correction.\n", encoding="utf-8")
        result = self.check(["legacy-plugin-compatibility"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("must include a strict version bump", result.stderr)

    def test_security_label_accepts_package_scoped_versioned_fix(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        self.write_package("demo", "1.0.2")
        result = self.check(["legacy-plugin-security"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("security exception accepted", result.stdout)

    def test_exception_cannot_change_policy(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        self.write_policy("2026-07-20")
        result = self.check(["legacy-plugin-compatibility"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot change or remove", result.stderr)

    def test_compatibility_label_allows_root_policy_readme_correction(self) -> None:
        self.adopt_policy_on_main()
        root_readme = self.repo / "plugins" / "README.md"
        root_readme.write_text("Original policy summary.\n", encoding="utf-8")
        self.commit("add policy readme")
        self.branch()
        root_readme.write_text("Corrected policy summary.\n", encoding="utf-8")
        result = self.check(["legacy-plugin-compatibility"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def write_root_readme(self, earliest: str) -> None:
        (self.repo / "plugins" / "README.md").write_text(
            f"Frozen policy; removal not before {earliest}.\n", encoding="utf-8"
        )

    def write_package_readme(self, name: str, earliest: str) -> None:
        (self.repo / "plugins" / name / "README.md").write_text(
            f"Deprecated fixture; removal not before {earliest}.\n", encoding="utf-8"
        )

    def test_removal_label_accepts_complete_date_amendment(self) -> None:
        self.adopt_policy_on_main()
        self.write_root_readme("2026-10-20")
        self.write_package_readme("demo", "2026-10-20")
        self.commit("date-quoting notice surfaces")
        self.branch()
        self.write_policy("2026-07-20")
        self.write_package("demo", "1.0.2")
        self.write_root_readme("2026-07-20")
        self.write_package_readme("demo", "2026-07-20")
        result = self.check(["legacy-plugin-removal"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("removal-date amendment exception accepted", result.stdout)

    def test_amendment_must_update_every_notice_surface(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        self.write_policy("2026-07-20")
        self.write_package("demo", "1.0.2")
        result = self.check(["legacy-plugin-removal"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("untouched: plugins/README.md, plugins/demo/README.md", result.stderr)

    def test_amendment_may_change_only_the_removal_date(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        path = self.repo / "plugins" / "deprecation.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        policy["earliest_removal"] = "2026-07-20"
        policy["packages"]["extra"] = {"deprecation_version": "1.0.0"}
        path.write_text(json.dumps(policy) + "\n", encoding="utf-8")
        result = self.check(["legacy-plugin-removal"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("may change only earliest_removal", result.stderr)

    def test_amendment_must_change_the_removal_date(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        path = self.repo / "plugins" / "deprecation.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(policy, indent=1) + "\n", encoding="utf-8")
        result = self.check(["legacy-plugin-removal"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("must change earliest_removal", result.stderr)

    def test_amendment_cannot_touch_frozen_payloads(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        self.write_policy("2026-07-20")
        payload = self.repo / "plugins" / "demo" / "commands" / "demo.md"
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text("Payload edit.\n", encoding="utf-8")
        self.git("add", "--all")
        result = self.check(["legacy-plugin-removal"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("must delete the entire plugins/ tree", result.stderr)

    def test_removal_is_date_gated_and_all_at_once(self) -> None:
        self.adopt_policy_on_main()
        self.branch()
        shutil.rmtree(self.repo / "plugins")
        early = self.check(["legacy-plugin-removal"], "2026-10-19")
        self.assertEqual(early.returncode, 1)
        self.assertIn("blocked until 2026-10-20", early.stderr)
        allowed = self.check(["legacy-plugin-removal"], "2026-10-20")
        self.assertEqual(allowed.returncode, 0, allowed.stderr)


if __name__ == "__main__":
    unittest.main()
