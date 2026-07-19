#!/usr/bin/env python3
"""Regression tests for the strict portable skill frontmatter parser."""

from __future__ import annotations

import tempfile
import shutil
import unittest
from pathlib import Path

from skill_catalog import compare_trees, parse_skill, validate_provenance
from sync_vendored_skills import copy_tree_atomically


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


class VendoredTreeSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="vendored-tree-test."))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)

    def test_comparison_rejects_symlink_in_source_tree(self) -> None:
        source = self.directory / "source"
        destination = self.directory / "destination"
        source.mkdir()
        destination.mkdir()
        private = self.directory / "private.txt"
        private.write_text("Invented private fixture.\n", encoding="utf-8")
        (source / "leak.txt").symlink_to(private)

        errors = compare_trees(source, destination)

        self.assertTrue(any("leak.txt" in error and "symlink" in error for error in errors))

    def test_atomic_copy_refuses_to_dereference_symlink(self) -> None:
        source = self.directory / "source"
        destination = self.directory / "copies" / "source"
        source.mkdir()
        private = self.directory / "private.txt"
        private.write_text("Invented private fixture.\n", encoding="utf-8")
        (source / "leak.txt").symlink_to(private)

        with self.assertRaisesRegex(ValueError, "symlink"):
            copy_tree_atomically(source, destination)

        self.assertFalse(destination.exists())


class ComposedProvenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="provenance-test."))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)

    def test_composed_skill_cannot_claim_no_vendored_content(self) -> None:
        (self.directory / "PROVENANCE.md").write_text(
            "# Provenance — invented\n\nNo vendored content. Invented local files only.\n",
            encoding="utf-8",
        )
        errors: list[str] = []

        validate_provenance(self.directory, errors, ("invented-reference",))

        self.assertTrue(any("is false for a composed skill" in error for error in errors))

    def test_composed_local_skill_can_delegate_bundled_provenance(self) -> None:
        delegated = self.directory / "references" / "invented-reference" / "PROVENANCE.md"
        delegated.parent.mkdir(parents=True)
        delegated.write_text("Invented delegated record.\n", encoding="utf-8")
        (self.directory / "PROVENANCE.md").write_text(
            "# Provenance — invented\n\n"
            "The root workflow is original local content.\n\n"
            "## Bundled reference provenance\n\n"
            "- `references/invented-reference/PROVENANCE.md`\n",
            encoding="utf-8",
        )
        errors: list[str] = []

        validate_provenance(self.directory, errors, ("invented-reference",))

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
