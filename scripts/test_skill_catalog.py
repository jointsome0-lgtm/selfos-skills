#!/usr/bin/env python3
"""Regression tests for the strict portable skill frontmatter parser."""

from __future__ import annotations

import tempfile
import shutil
import unittest
from pathlib import Path

from build_index import (
    README_COMPATIBILITY_END,
    README_COMPATIBILITY_START,
    rendered_adapter_manifest,
    updated_readme,
)
from skill_catalog import (
    ALLOWED_FIELDS,
    compatibility_errors,
    compare_trees,
    derive_adapter_version,
    parse_skill,
    validate_provenance,
    version_errors,
)
from build_bundles import copy_tree_atomically


class SkillCatalogParserTest(unittest.TestCase):
    def write_skill(self, description: str, extra_frontmatter: str = "") -> Path:
        directory = Path(tempfile.mkdtemp(prefix="skill-catalog-test."))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "SKILL.md"
        path.write_text(
            "---\n"
            "name: invented-skill\n"
            f"description: {description}\n"
            f"{extra_frontmatter}"
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

    def test_host_only_top_level_field_is_not_portable(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing host neutrality.",
            "compatibility: No runtime requirements.\n"
            "argument-hint: invented\n",
        )

        skill, errors = parse_skill(path)

        self.assertEqual(errors, [])
        self.assertIsNotNone(skill)
        assert skill is not None
        self.assertNotIn("argument-hint", ALLOWED_FIELDS)
        self.assertIn("argument-hint", set(skill.fields) - ALLOWED_FIELDS)

    def test_disable_model_invocation_is_the_documented_exception(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing host neutrality.",
            "compatibility: No runtime requirements.\n"
            "disable-model-invocation: true\n",
        )

        skill, errors = parse_skill(path)

        self.assertEqual(errors, [])
        self.assertIsNotNone(skill)
        assert skill is not None
        self.assertIn("disable-model-invocation", ALLOWED_FIELDS)
        self.assertNotIn("disable-model-invocation", set(skill.fields) - ALLOWED_FIELDS)

    def test_version_is_namespaced_metadata_not_a_top_level_extension(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing canonical versions.",
            "compatibility: No runtime requirements.\n"
            "metadata:\n"
            '  selfos.version: "1.2.3"\n',
        )

        skill, errors = parse_skill(path)

        self.assertEqual(errors, [])
        assert skill is not None
        self.assertEqual(skill.version, "1.2.3")
        self.assertNotIn("version", ALLOWED_FIELDS)
        self.assertEqual(version_errors(skill), [])

    def test_missing_canonical_version_is_rejected(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing canonical versions.",
            "compatibility: No runtime requirements.\n",
        )
        skill, errors = parse_skill(path)
        self.assertEqual(errors, [])
        assert skill is not None

        self.assertTrue(any("selfos.version is required" in error for error in version_errors(skill)))

    def test_adapter_version_is_component_wise_skill_sum(self) -> None:
        first_path = self.write_skill(
            "Runs an invented workflow. Use when testing derived versions.",
            "compatibility: No runtime requirements.\n"
            "metadata:\n"
            '  selfos.version: "1.2.3"\n',
        )
        second_path = self.write_skill(
            "Runs an invented workflow. Use when testing derived versions.",
            "compatibility: No runtime requirements.\n"
            "metadata:\n"
            '  selfos.version: "0.4.5"\n',
        )
        first, first_errors = parse_skill(first_path)
        second, second_errors = parse_skill(second_path)
        self.assertEqual(first_errors + second_errors, [])
        assert first is not None and second is not None

        version, errors = derive_adapter_version((first, second))

        self.assertEqual(errors, [])
        self.assertEqual(version, "1.6.8")

    def test_shell_helper_requires_bash_declaration(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing compatibility.",
            "compatibility: Requires network access.\n",
        )
        scripts = path.parent / "scripts"
        scripts.mkdir()
        (scripts / "invented-helper.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        skill, errors = parse_skill(path)
        self.assertEqual(errors, [])
        assert skill is not None

        declared_errors = compatibility_errors(skill)

        self.assertTrue(any("must declare bash" in error for error in declared_errors))

    def test_compatibility_declaration_is_required(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing compatibility."
        )
        skill, errors = parse_skill(path)
        self.assertEqual(errors, [])
        assert skill is not None

        declared_errors = compatibility_errors(skill)

        self.assertTrue(any("missing required field 'compatibility'" in error for error in declared_errors))

    def test_vendored_python_helper_requires_python_declaration(self) -> None:
        path = self.write_skill(
            "Runs an invented workflow. Use when testing compatibility.",
            "compatibility: Host-neutral Markdown guidance.\n",
        )
        scripts = path.parent / "references" / "invented" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "invented_helper.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        skill, errors = parse_skill(path)
        self.assertEqual(errors, [])
        assert skill is not None

        declared_errors = compatibility_errors(skill)

        self.assertTrue(any("must declare python" in error for error in declared_errors))


class ReadmeCompatibilityGenerationTest(unittest.TestCase):
    def test_inserts_and_then_replaces_generated_block(self) -> None:
        original = "# Invented catalog\n\n## Repository layout\n\nInvented layout.\n"
        first_block = (
            f"{README_COMPATIBILITY_START}\n## Compatibility\n\nFirst.\n"
            f"{README_COMPATIBILITY_END}\n"
        )
        inserted, errors = updated_readme(original, first_block)
        self.assertEqual(errors, [])
        assert inserted is not None
        self.assertIn(first_block, inserted)

        second_block = first_block.replace("First.", "Second.")
        replaced, errors = updated_readme(inserted, second_block)

        self.assertEqual(errors, [])
        assert replaced is not None
        self.assertIn("Second.", replaced)
        self.assertNotIn("First.", replaced)
        self.assertEqual(replaced.count(README_COMPATIBILITY_START), 1)

    def test_rejects_incomplete_generated_markers(self) -> None:
        actual = f"# Invented catalog\n\n{README_COMPATIBILITY_START}\n"

        updated, errors = updated_readme(actual, "Invented block.\n")

        self.assertIsNone(updated)
        self.assertTrue(any("incomplete or duplicate" in error for error in errors))


class AdapterManifestGenerationTest(unittest.TestCase):
    def test_rewrites_only_the_single_version_field(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="adapter-manifest-test."))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "plugin.json"
        actual = (
            "{\n"
            '  "name": "invented",\n'
            '  "version": "0.1.0",\n'
            '  "author": { "name": "Invented" }\n'
            "}\n"
        )
        path.write_text(actual, encoding="utf-8")

        rendered, errors = rendered_adapter_manifest(path, "1.6.8")

        self.assertEqual(errors, [])
        self.assertEqual(rendered, actual.replace('"0.1.0"', '"1.6.8"'))

    def test_rejects_ambiguous_version_fields(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="adapter-manifest-test."))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "plugin.json"
        path.write_text(
            '{\n  "version": "0.1.0",\n  "nested": {\n    "version": "2.0.0"\n  }\n}\n',
            encoding="utf-8",
        )

        rendered, errors = rendered_adapter_manifest(path, "0.2.0")

        self.assertIsNone(rendered)
        self.assertTrue(any("exactly one" in error for error in errors))


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
