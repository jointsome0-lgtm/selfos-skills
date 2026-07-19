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

    def branch(self, name: str = "feature") -> None:
        self.git("checkout", "--quiet", "-b", name)

    def check(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--base", "main", *argv],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )

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

    def touch_plugin_skill(self, name: str, line: str) -> None:
        skill = self.repo / "plugins" / name / "skills" / name / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + line + "\n", encoding="utf-8")

    def write_adapter(self, manifest_dir: str, version: str) -> None:
        manifest = self.repo / manifest_dir / "plugin.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps({"name": "aggregate", "version": version, "description": "Invented."})
            + "\n",
            encoding="utf-8",
        )

    def write_adapters(self, version: str) -> None:
        self.write_adapter(".claude-plugin", version)
        self.write_adapter(".codex-plugin", version)

    def write_canonical_skill(
        self,
        name: str,
        version: str | None,
        body: str = "Invented canonical body.",
    ) -> None:
        path = self.repo / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = (
            f'metadata:\n  selfos.version: "{version}"\n'
            if version is not None
            else ""
        )
        path.write_text(
            "---\n"
            f"name: {name}\n"
            "description: Runs an invented workflow. Use when testing version mechanics.\n"
            f"{metadata}"
            "---\n\n"
            f"# {name}\n\n{body}\n",
            encoding="utf-8",
        )

    def set_up_catalog(self, version: str = "1.0.0") -> None:
        self.write_canonical_skill("catalog-demo", version)
        self.write_adapters(version)
        self.commit("add canonical catalog")

    def test_legacy_content_change_without_bump_fails(self) -> None:
        self.branch()
        self.touch_plugin_skill("demo", "Invented edit without a bump.")
        self.commit("edit legacy skill")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("plugins/demo", result.stderr)
        self.assertIn("bump plugins/demo/.claude-plugin/plugin.json", result.stderr)

    def test_legacy_content_change_with_bump_passes(self) -> None:
        self.branch()
        self.touch_plugin_skill("demo", "Invented edit shipped with a bump.")
        self.write_plugin("demo", "1.0.1")
        self.commit("edit legacy skill and bump")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 changed legacy plugin(s)", result.stdout)

    def test_legacy_bump_only_diff_passes(self) -> None:
        self.branch()
        self.write_plugin("demo", "1.1.0")
        self.commit("legacy bump only")
        self.assertEqual(self.check().returncode, 0)

    def test_new_legacy_plugin_passes(self) -> None:
        self.branch()
        self.write_plugin("fresh", "0.1.0")
        self.commit("add fresh legacy plugin")
        self.assertEqual(self.check().returncode, 0)

    def test_deleted_legacy_plugin_passes(self) -> None:
        self.branch()
        shutil.rmtree(self.repo / "plugins" / "demo")
        self.commit("remove legacy plugin")
        self.assertEqual(self.check().returncode, 0)

    def test_change_outside_guarded_roots_passes(self) -> None:
        self.branch()
        (self.repo / "README.md").write_text("Invented update.\n", encoding="utf-8")
        self.commit("update readme")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no guarded content changes", result.stdout)

    def test_uncommitted_legacy_change_without_bump_fails(self) -> None:
        self.branch()
        self.touch_plugin_skill("demo", "Invented uncommitted edit.")
        self.assertEqual(self.check().returncode, 1)

    def test_names_only_the_unbumped_legacy_plugin(self) -> None:
        self.write_plugin("extra", "2.0.0")
        self.commit("add extra legacy plugin")
        self.branch()
        self.touch_plugin_skill("demo", "Invented bumped edit.")
        self.write_plugin("demo", "1.0.1")
        self.touch_plugin_skill("extra", "Invented unbumped edit.")
        self.commit("edit both legacy plugins")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("plugins/extra", result.stderr)
        self.assertNotIn("plugins/demo:", result.stderr)

    def test_canonical_content_change_without_skill_bump_fails(self) -> None:
        self.set_up_catalog()
        self.branch()
        self.write_canonical_skill("catalog-demo", "1.0.0", "Changed canonical body.")
        self.commit("edit canonical skill")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("skills/catalog-demo", result.stderr)
        self.assertIn("metadata.selfos.version stayed", result.stderr)

    def test_canonical_content_change_with_skill_bump_passes(self) -> None:
        self.set_up_catalog()
        self.branch()
        self.write_canonical_skill("catalog-demo", "1.0.1", "Changed canonical body.")
        self.write_adapters("1.0.1")
        self.commit("edit and bump canonical skill")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 changed canonical skill(s)", result.stdout)
        self.assertIn("adapter version 1.0.1 is current", result.stdout)

    def test_canonical_bump_only_diff_passes(self) -> None:
        self.set_up_catalog()
        self.branch()
        self.write_canonical_skill("catalog-demo", "1.0.1")
        self.write_adapters("1.0.1")
        self.commit("canonical bump only")
        self.assertEqual(self.check().returncode, 0)

    def test_manifest_drift_fails_even_when_skill_bumped(self) -> None:
        self.set_up_catalog()
        self.branch()
        self.write_canonical_skill("catalog-demo", "1.0.1", "Changed canonical body.")
        self.commit("forget generated adapters")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(".claude-plugin/plugin.json: derived version is stale", result.stderr)
        self.assertIn(".codex-plugin/plugin.json: derived version is stale", result.stderr)

    def test_component_wise_sum_derives_adapter_version(self) -> None:
        self.write_canonical_skill("catalog-demo", "1.2.3")
        self.write_canonical_skill("catalog-extra", "0.4.5")
        self.write_adapters("1.6.8")
        self.commit("add summed catalog")
        self.branch()
        self.write_canonical_skill("catalog-demo", "1.3.0")
        self.write_adapters("1.7.5")
        self.commit("minor bump resets one patch")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("adapter version 1.7.5 is current", result.stdout)

    def test_one_time_version_adoption_passes(self) -> None:
        self.write_canonical_skill("catalog-demo", None)
        self.write_adapters("0.1.0")
        self.commit("add unversioned predecessor")
        self.branch()
        self.write_canonical_skill("catalog-demo", "0.1.0")
        self.commit("adopt canonical version")
        self.assertEqual(self.check().returncode, 0)

    def test_new_canonical_skill_updates_derived_version(self) -> None:
        self.write_canonical_skill("catalog-demo", "0.1.0")
        self.write_adapters("0.1.0")
        self.commit("add first canonical skill")
        self.branch()
        self.write_canonical_skill("catalog-extra", "0.1.0")
        self.write_adapters("0.2.0")
        self.commit("add second canonical skill")
        self.assertEqual(self.check().returncode, 0)

    def test_deleted_canonical_skill_fails(self) -> None:
        self.set_up_catalog()
        self.branch()
        shutil.rmtree(self.repo / "skills" / "catalog-demo")
        self.commit("remove canonical skill")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical SKILL.md was removed", result.stderr)

    def test_canonical_version_downgrade_fails(self) -> None:
        self.set_up_catalog()
        self.branch()
        self.write_canonical_skill("catalog-demo", "0.9.0")
        self.write_adapters("0.9.0")
        self.commit("downgrade canonical skill")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("version decreased", result.stderr)

    def test_vendored_change_requires_composed_skill_bump(self) -> None:
        self.write_canonical_skill("catalog-demo", "0.1.0")
        self.write_canonical_skill("catalog-wrapper", "0.1.0")
        reference = self.repo / "skills" / "catalog-wrapper" / "references" / "catalog-demo"
        reference.mkdir(parents=True)
        (reference / "invented.txt").write_text("Original.\n", encoding="utf-8")
        self.write_adapters("0.2.0")
        self.commit("add composed catalog")
        self.branch()
        (reference / "invented.txt").write_text("Changed.\n", encoding="utf-8")
        self.commit("sync changed vendored content")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("skills/catalog-wrapper", result.stderr)

    def test_invalid_head_skill_version_is_reported(self) -> None:
        self.set_up_catalog()
        self.branch()
        self.write_canonical_skill("catalog-demo", "01.0.0")
        self.commit("write invalid canonical version")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no leading zeroes", result.stderr)

    def test_unresolvable_base_is_reported(self) -> None:
        result = self.check("--base", "no-such-ref")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not resolve", result.stderr)

    def test_invalid_head_legacy_manifest_is_reported(self) -> None:
        self.branch()
        manifest = self.repo / "plugins" / "demo" / ".claude-plugin" / "plugin.json"
        manifest.write_text("{not json", encoding="utf-8")
        self.commit("break legacy manifest")
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("invalid JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
