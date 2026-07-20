#!/usr/bin/env python3
"""Regression tests for the composed-skill bundle builder and its diagnostics."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from build_bundles import (
    GITATTRIBUTES_BEGIN,
    GITATTRIBUTES_END,
    expected_gitattributes,
    gitattributes_lines,
    graph_errors,
    render_marker,
    run,
)
from skill_catalog import (
    BUNDLE_MANIFEST_NAME,
    GENERATED_MARKER_NAME,
    Skill,
    load_bundle_manifest,
    parse_skill,
)


class BundleManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="bundle-manifest-test."))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)

    def write_manifest(self, payload: object) -> None:
        (self.directory / BUNDLE_MANIFEST_NAME).write_text(
            payload if isinstance(payload, str) else json.dumps(payload),
            encoding="utf-8",
        )

    def test_missing_manifest_means_no_bundle(self) -> None:
        dependencies, errors = load_bundle_manifest(self.directory)

        self.assertIsNone(dependencies)
        self.assertEqual(errors, [])

    def test_valid_manifest_returns_dependencies(self) -> None:
        self.write_manifest({"dependencies": ["invented-first", "invented-second"]})

        dependencies, errors = load_bundle_manifest(self.directory)

        self.assertEqual(errors, [])
        self.assertEqual(dependencies, ("invented-first", "invented-second"))

    def test_non_object_manifest_is_rejected(self) -> None:
        self.write_manifest(["invented"])

        dependencies, errors = load_bundle_manifest(self.directory)

        self.assertIsNone(dependencies)
        self.assertTrue(any("top-level JSON value must be an object" in error for error in errors))

    def test_unknown_keys_are_rejected(self) -> None:
        self.write_manifest({"dependencies": ["invented"], "extras": True})

        _, errors = load_bundle_manifest(self.directory)

        self.assertTrue(any("unsupported manifest keys: extras" in error for error in errors))

    def test_empty_dependency_list_is_rejected(self) -> None:
        self.write_manifest({"dependencies": []})

        dependencies, errors = load_bundle_manifest(self.directory)

        self.assertIsNone(dependencies)
        self.assertTrue(any("must not be empty" in error for error in errors))

    def test_path_escaping_names_are_rejected(self) -> None:
        self.write_manifest({"dependencies": ["../escape", "nested/path"]})

        dependencies, errors = load_bundle_manifest(self.directory)

        self.assertIsNone(dependencies)
        matching = [error for error in errors if "invalid dependency name" in error]
        self.assertEqual(len(matching), 2)
        self.assertTrue(any("path separators" in error for error in matching))

    def test_duplicates_and_unsorted_lists_are_rejected(self) -> None:
        self.write_manifest({"dependencies": ["b-invented", "a-invented", "b-invented"]})

        dependencies, errors = load_bundle_manifest(self.directory)

        self.assertIsNone(dependencies)
        self.assertTrue(any("must not contain duplicates" in error for error in errors))
        self.assertTrue(any("sorted alphabetically" in error for error in errors))


class BundleGraphTest(unittest.TestCase):
    @staticmethod
    def invented_skill(name: str) -> Skill:
        return Skill(
            name=name,
            description="Invented. Use when testing.",
            path=Path(f"skills/{name}/SKILL.md"),
            root=Path(f"skills/{name}"),
            fields={},
            metadata={},
            body="Invented body.",
        )

    def test_unknown_dependency_is_actionable(self) -> None:
        known = {"alpha": self.invented_skill("alpha")}

        errors = graph_errors({"alpha": ("missing-invented",)}, known)

        self.assertTrue(
            any(
                "unknown dependency 'missing-invented'" in error
                and f"skills/alpha/{BUNDLE_MANIFEST_NAME}" in error
                for error in errors
            ),
            errors,
        )

    def test_self_bundle_is_rejected(self) -> None:
        known = {"alpha": self.invented_skill("alpha")}

        errors = graph_errors({"alpha": ("alpha",)}, known)

        self.assertTrue(any("cannot bundle itself" in error for error in errors))

    def test_nested_composition_requires_flattening(self) -> None:
        known = {name: self.invented_skill(name) for name in ("alpha", "beta", "gamma")}

        errors = graph_errors({"alpha": ("beta",), "beta": ("gamma",)}, known)

        self.assertTrue(
            any("is itself a composed skill" in error and "flat" in error for error in errors)
        )

    def test_cycle_is_reported_with_its_chain(self) -> None:
        known = {name: self.invented_skill(name) for name in ("alpha", "beta")}

        errors = graph_errors({"alpha": ("beta",), "beta": ("alpha",)}, known)

        self.assertTrue(
            any("dependency cycle: alpha -> beta -> alpha" in error for error in errors),
            errors,
        )


class BundleBuildTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="bundle-build-test."))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.gitattributes = self.repo / ".gitattributes"
        self.composed = self.write_skill(
            "composed-invented", dependencies=["leaf-invented"]
        )
        self.leaf = self.write_skill("leaf-invented")
        (self.leaf.root / "EXTRA.md").write_text("Invented reference.\n", encoding="utf-8")

    def write_skill(self, name: str, dependencies: list[str] | None = None) -> Skill:
        root = self.repo / "skills" / name
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            "description: Runs an invented workflow. Use when testing bundles.\n"
            "metadata:\n"
            '  selfos.version: "0.1.0"\n'
            "---\n\n# Invented\n",
            encoding="utf-8",
        )
        if dependencies is not None:
            (root / BUNDLE_MANIFEST_NAME).write_text(
                json.dumps({"dependencies": dependencies}) + "\n", encoding="utf-8"
            )
        skill, errors = parse_skill(root / "SKILL.md")
        assert skill is not None and errors == [], errors
        return skill

    def build(self, check: bool = False) -> tuple[int, list[str]]:
        skills = []
        for path in sorted((self.repo / "skills").glob("*/SKILL.md")):
            skill, errors = parse_skill(path)
            assert skill is not None and errors == [], errors
            skills.append(skill)
        return run(skills, check, self.gitattributes)

    def test_build_is_deterministic_and_marks_copies_generated(self) -> None:
        changed, problems = self.build()

        self.assertEqual(problems, [])
        self.assertGreater(changed, 0)
        destination = self.composed.root / "references" / "leaf-invented"
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assertTrue((destination / "EXTRA.md").is_file())
        marker = (destination / GENERATED_MARKER_NAME).read_text(encoding="utf-8")
        self.assertIn("do not edit", marker)
        self.assertIn("skills/leaf-invented/", marker)
        self.assertIn("version 0.1.0", marker)
        attributes = self.gitattributes.read_text(encoding="utf-8")
        self.assertIn(
            "skills/composed-invented/references/leaf-invented/** linguist-generated=true",
            attributes,
        )

        changed_again, problems_again = self.build()
        self.assertEqual((changed_again, problems_again), (0, []))
        self.assertEqual(self.build(check=True), (0, []))

    def test_check_reports_drift_and_build_repairs_it(self) -> None:
        self.build()
        vendored = self.composed.root / "references" / "leaf-invented" / "EXTRA.md"
        vendored.write_text("Edited the wrong copy.\n", encoding="utf-8")

        _, problems = self.build(check=True)

        self.assertTrue(any("vendored file drift" in problem and "EXTRA.md" in problem for problem in problems))
        self.assertTrue(any("run python scripts/build_bundles.py" in problem for problem in problems))

        changed, repair_problems = self.build()
        self.assertEqual(repair_problems, [])
        self.assertGreater(changed, 0)
        self.assertIn("Invented reference.", vendored.read_text(encoding="utf-8"))

    def test_check_reports_marker_drift(self) -> None:
        self.build()
        marker = self.composed.root / "references" / "leaf-invented" / GENERATED_MARKER_NAME
        marker.write_text("Forged marker.\n", encoding="utf-8")

        _, problems = self.build(check=True)

        self.assertTrue(any("generated marker drift" in problem for problem in problems))

    def test_stale_generated_tree_is_reported_and_removed(self) -> None:
        self.build()
        stale = self.composed.root / "references" / "gone-invented"
        stale.mkdir()
        (stale / GENERATED_MARKER_NAME).write_text("Old marker.\n", encoding="utf-8")

        _, problems = self.build(check=True)
        self.assertTrue(any("stale generated bundle" in problem for problem in problems))

        changed, build_problems = self.build()
        self.assertEqual(build_problems, [])
        self.assertGreater(changed, 0)
        self.assertFalse(stale.exists())

    def test_authored_reference_material_is_never_touched(self) -> None:
        authored = self.composed.root / "references" / "authored-invented"
        authored.mkdir(parents=True)
        (authored / "NOTES.md").write_text("Hand-written notes.\n", encoding="utf-8")

        self.build()
        _, problems = self.build(check=True)

        self.assertEqual(problems, [])
        self.assertTrue((authored / "NOTES.md").is_file())

    def test_reserved_marker_in_canonical_source_is_rejected(self) -> None:
        (self.leaf.root / GENERATED_MARKER_NAME).write_text("Not generated.\n", encoding="utf-8")

        _, problems = self.build(check=True)

        self.assertTrue(any("reserved for generated bundle metadata" in problem for problem in problems))

    def test_missing_dependency_fails_before_touching_the_tree(self) -> None:
        shutil.rmtree(self.leaf.root)

        changed, problems = self.build(check=False)

        self.assertEqual(changed, 0)
        self.assertTrue(any("unknown dependency 'leaf-invented'" in problem for problem in problems))


class GitattributesBlockTest(unittest.TestCase):
    def test_block_is_appended_then_replaced_in_place(self) -> None:
        lines = gitattributes_lines({"alpha": ("beta",)})
        appended, errors = expected_gitattributes("*.invented text\n", lines)

        self.assertEqual(errors, [])
        assert appended is not None
        self.assertTrue(appended.startswith("*.invented text\n"))
        self.assertIn(GITATTRIBUTES_BEGIN, appended)
        self.assertIn("skills/alpha/references/beta/** linguist-generated=true", appended)

        replaced, errors = expected_gitattributes(
            appended, gitattributes_lines({"alpha": ("gamma",)})
        )
        self.assertEqual(errors, [])
        assert replaced is not None
        self.assertEqual(replaced.count(GITATTRIBUTES_BEGIN), 1)
        self.assertIn("skills/alpha/references/gamma/**", replaced)
        self.assertNotIn("references/beta/**", replaced)

    def test_incomplete_markers_are_rejected(self) -> None:
        text = f"{GITATTRIBUTES_BEGIN}\n"

        expected, errors = expected_gitattributes(text, [])

        self.assertIsNone(expected)
        self.assertTrue(any("incomplete or duplicate" in error for error in errors))

    def test_no_bundles_leaves_a_plain_file_untouched(self) -> None:
        expected, errors = expected_gitattributes("*.invented text\n", [])

        self.assertEqual(errors, [])
        self.assertEqual(expected, "*.invented text\n")

    def test_marker_content_is_deterministic(self) -> None:
        composed = BundleGraphTest.invented_skill("alpha")
        dependency = BundleGraphTest.invented_skill("beta")

        self.assertEqual(
            render_marker(composed, dependency), render_marker(composed, dependency)
        )


if __name__ == "__main__":
    unittest.main()
