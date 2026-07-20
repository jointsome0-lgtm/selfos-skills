#!/usr/bin/env python3
"""Regression tests for legacy package validation shared with main."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import validate_plugins as validator
from validate_plugins import migration_command, required_text


class RequiredTextTest(unittest.TestCase):
    def test_plain_non_empty_text_passes(self) -> None:
        errors: list[str] = []

        value = required_text(
            {"description": "Invented compatibility package."},
            "description",
            "invented.json",
            errors,
        )

        self.assertEqual(value, "Invented compatibility package.")
        self.assertEqual(errors, [])

    def test_control_character_is_rejected(self) -> None:
        errors: list[str] = []

        value = required_text(
            {"description": "Invented\ncompatibility package."},
            "description",
            "invented.json",
            errors,
        )

        self.assertIsNone(value)
        self.assertEqual(
            errors,
            ["invented.json: 'description' must not contain control characters"],
        )

    def test_migration_command_keeps_policy_skill_order(self) -> None:
        self.assertEqual(
            migration_command("invented/example", ["first-skill", "second-skill"]),
            "npx skills add invented/example --skill first-skill second-skill "
            "--agent claude-code --global --yes",
        )

    def test_package_notice_validator_rejects_missing_manifest_notice(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="plugin-notice-test."))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        package = root / "plugins" / "invented"
        manifest = package / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        (root / "skills" / "invented-skill").mkdir(parents=True)
        (root / "skills" / "invented-skill" / "SKILL.md").write_text(
            "Invented canonical skill.\n", encoding="utf-8"
        )
        manifest.write_text(
            json.dumps(
                {
                    "name": "invented",
                    "version": "1.0.1",
                    "description": "Ordinary description without a notice.",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        issue = "https://github.com/invented/example/issues/1"
        command = migration_command("invented/example", ["invented-skill"])
        (package / "README.md").write_text(
            "\n".join(
                (
                    "# `invented@selfos` is deprecated",
                    "Version 1.0.1.",
                    command,
                    "/plugin update invented@selfos",
                    "/plugin uninstall invented@selfos",
                    "Not before 2026-10-20.",
                    issue,
                    "downstream repositories",
                    "installation smoke matrix",
                    "major-migration release note",
                )
            ),
            encoding="utf-8",
        )
        policy = {
            "canonical_source": "invented/example",
            "earliest_removal": "2026-10-20",
            "removal_issue": issue,
            "packages": {
                "invented": {
                    "deprecation_version": "1.0.1",
                    "canonical_skills": ["invented-skill"],
                }
            },
        }
        errors: list[str] = []
        with mock.patch.multiple(
            validator,
            ROOT=root,
            PLUGINS=root / "plugins",
            DEPRECATION=root / "plugins" / "deprecation.json",
        ):
            validator.validate_deprecation_notice("invented", package, policy, errors)
        self.assertTrue(any("complete deprecation notice" in error for error in errors))

    def test_missing_policy_is_valid_only_when_optional(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="plugin-removal-test."))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        missing = root / "plugins" / "deprecation.json"
        optional_errors: list[str] = []
        required_errors: list[str] = []
        with mock.patch.multiple(
            validator,
            ROOT=root,
            PLUGINS=root / "plugins",
            DEPRECATION=missing,
        ):
            self.assertIsNone(
                validator.load_deprecation(optional_errors, required=False)
            )
            self.assertIsNone(
                validator.load_deprecation(required_errors, required=True)
            )
        self.assertEqual(optional_errors, [])
        self.assertEqual(required_errors, ["plugins/deprecation.json: missing"])

    def test_aggregate_only_post_removal_layout_passes(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="plugin-removal-layout-test."))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        scripts = root / "scripts"
        manifests = root / ".claude-plugin"
        scripts.mkdir()
        manifests.mkdir()
        shutil.copy2(Path(validator.__file__), scripts / "validate_plugins.py")
        shutil.copy2(Path(validator.__file__).with_name("skill_catalog.py"), scripts)
        (manifests / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "selfos-skills",
                    "version": "1.0.0",
                    "description": "Invented aggregate.",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (manifests / "marketplace.json").write_text(
            json.dumps(
                {
                    "name": "selfos",
                    "owner": {"name": "Invented"},
                    "plugins": [
                        {
                            "name": "selfos-skills",
                            "source": "./",
                            "description": "Invented aggregate.",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, str(scripts / "validate_plugins.py")],
            cwd=root,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 legacy packages", result.stdout)


if __name__ == "__main__":
    unittest.main()
