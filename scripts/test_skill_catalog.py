#!/usr/bin/env python3
"""Regression tests for the strict portable skill frontmatter parser."""

from __future__ import annotations

import tempfile
import shutil
import unittest
from pathlib import Path

from skill_catalog import parse_skill


class SkillCatalogParserTest(unittest.TestCase):
    def write_skill(self, description: str) -> Path:
        directory = Path(tempfile.mkdtemp(prefix="skill-catalog-test."))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "SKILL.md"
        path.write_text(
            "---\n"
            "name: invented-skill\n"
            f"description: {description}\n"
            "---\n"
            "\n"
            "# Invented skill\n",
            encoding="utf-8",
        )
        return path

    def test_doubled_apostrophe_in_single_quoted_scalar_is_decoded(self) -> None:
        path = self.write_skill(
            "'Reviews the owner''s invented plan. Use when testing valid frontmatter.'"
        )

        skill, errors = parse_skill(path)

        self.assertEqual(errors, [])
        self.assertIsNotNone(skill)
        assert skill is not None
        self.assertEqual(
            skill.description,
            "Reviews the owner's invented plan. Use when testing valid frontmatter.",
        )

    def test_undoubled_apostrophe_reaches_validator_error_path(self) -> None:
        path = self.write_skill(
            "'Reviews the owner's invented plan. Use when testing invalid frontmatter.'"
        )

        skill, errors = parse_skill(path)

        self.assertIsNone(skill)
        self.assertTrue(
            any(
                "apostrophes in single-quoted frontmatter must be doubled" in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
