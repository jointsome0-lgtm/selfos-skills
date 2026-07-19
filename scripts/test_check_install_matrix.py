#!/usr/bin/env python3
"""Unit tests for the installation smoke-test matrix helpers."""

from pathlib import Path
import tempfile
import unittest

import check_install_matrix as smoke


class InstallSmokeMatrixTests(unittest.TestCase):
    def test_matrix_has_required_unique_cases(self) -> None:
        matrix = smoke.load_matrix()
        case_ids = {case["id"] for case in matrix["cases"]}
        self.assertTrue(
            {
                "npx-catalog",
                "codex-installer",
                "claude-code-installer",
                "cursor-installer",
                "opencode-installer",
                "codex-native",
                "claude-root-and-legacy",
            }.issubset(case_ids)
        )

    def test_exact_set_error_names_missing_and_unexpected_skills(self) -> None:
        with self.assertRaisesRegex(
            smoke.SmokeFailure,
            r"missing skill: compose; unexpected skill: invented-skill",
        ):
            smoke.assert_exact_set(
                "fixture", {"compose", "watch"}, {"invented-skill", "watch"}, "skill"
            )

    def test_skill_tree_checks_companions_modes_and_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "checkout"
            canonical = root / "skills"
            installed = Path(temporary) / "installed"
            for base in (canonical, installed):
                (base / "deepen" / "references" / "codebase-design").mkdir(parents=True)
                (base / "watch" / "scripts").mkdir(parents=True)
                (base / "deepen" / "SKILL.md").write_text("deepen\n", encoding="utf-8")
                (base / "deepen" / "references" / "codebase-design" / "SKILL.md").write_text(
                    "composed\n", encoding="utf-8"
                )
                (base / "watch" / "SKILL.md").write_text("watch\n", encoding="utf-8")
                helper = base / "watch" / "scripts" / "codex-pr-watch.sh"
                helper.write_text("#!/bin/sh\n", encoding="utf-8")
                helper.chmod(0o755)

            smoke.assert_skill_tree(canonical, installed, root)
            (installed / "watch" / "scripts" / "codex-pr-watch.sh").write_text(
                str(root), encoding="utf-8"
            )
            with self.assertRaisesRegex(smoke.SmokeFailure, "changed companion file"):
                smoke.assert_skill_tree(canonical, installed, root)


if __name__ == "__main__":
    unittest.main()
