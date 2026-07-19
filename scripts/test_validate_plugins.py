#!/usr/bin/env python3
"""Regression tests for legacy package validation shared with main."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
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


if __name__ == "__main__":
    unittest.main()
