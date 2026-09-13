#!/usr/bin/env python3
"""Exercise the standalone command on invented memory files."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("check_core.py")


class CoreCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.write("direction.txt", "direction")
        self.write("current.txt", "current")
        self.write("later.txt", "later")

    def write(self, name, text):
        (self.root / name).write_bytes(text.encode("utf-8"))

    def check(self, *arguments, script=SCRIPT):
        result = subprocess.run(
            [sys.executable, "-B", str(script), *arguments],
            cwd=self.root, capture_output=True, text=True,
            env={**os.environ, "PATH": ""},
        )
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_combines_files_and_measures_deferred_separately(self):
        code, result = self.check(
            "--active", "direction.txt", "current.txt", "--target", "100",
            "--deferred", "later.txt", "--deferred-target", "10",
        )
        self.assertEqual((code, result["status"]), (0, "ok"))
        self.assertEqual(result["groups"]["active"]["characters"], 16)
        self.assertEqual(result["groups"]["deferred"]["characters"], 5)
        self.write("later.txt", "x" * 14)
        code, result = self.check(
            "--active", "current.txt", "--target", "100",
            "--deferred", "later.txt", "--deferred-target", "10",
        )
        self.assertEqual((code, result["status"]), (1, "review_due"))
        self.assertFalse(result["groups"]["active"]["review_due"])
        self.assertTrue(result["groups"]["deferred"]["review_due"])

    def test_counts_unicode_and_crlf_at_the_rounded_boundary(self):
        self.write("context with spaces.txt", "\ufeff" + "я" * 131 + "\r\n")
        args = ("--active", "context with spaces.txt", "--target", "101")
        code, result = self.check(*args)
        group = result["groups"]["active"]
        self.assertEqual((code, group["characters"], group["review_at"]), (0, 134, 135))
        self.write("context with spaces.txt", "\ufeff" + "я" * 132 + "\r\n")
        code, result = self.check(*args)
        self.assertEqual((code, result["status"]), (1, "review_due"))
        self.assertEqual(result["groups"]["active"]["characters"], 135)

    def test_custom_margin_and_single_file_need_no_deferred_group(self):
        for margin, size, expected in [(0, 99, 0), (0, 100, 1), (50, 149, 0), (50, 150, 1)]:
            with self.subTest(margin=margin, size=size):
                self.write("current.txt", "x" * size)
                code, result = self.check(
                    "--active", "current.txt", "--target", "100",
                    "--margin-percent", str(margin),
                )
                self.assertEqual(code, expected)
                self.assertEqual(set(result["groups"]), {"active"})

    def test_invalid_arguments_return_json_errors(self):
        for args in [
            (),
            ("--active", "current.txt", "--target", "0"),
            ("--active", "current.txt", "--target", "bad"),
            ("--active", "current.txt", "--target", "10", "--margin-percent", "-1"),
            ("--active", "current.txt", "--target", "10", "--margin-percent", "0.33"),
            ("--active", "current.txt", "--target", "10", "--deferred", "later.txt"),
            ("--active", "current.txt", "--target", "10", "--deferred-target", "10"),
        ]:
            with self.subTest(args=args):
                code, result = self.check(*args)
                self.assertEqual((code, result["status"]), (2, "error"))

    def test_input_errors_and_duplicate_paths_fail_without_a_partial_verdict(self):
        (self.root / "broken.txt").write_bytes(b"\xff")
        (self.root / "folder").mkdir()
        for paths in [("missing.txt",), ("broken.txt",), ("folder",), ("current.txt", "./current.txt")]:
            with self.subTest(paths=paths):
                code, result = self.check("--active", *paths, "--target", "100")
                self.assertEqual((code, result["status"]), (2, "error"))
                self.assertNotIn("groups", result)
        code, result = self.check(
            "--active", "current.txt", "--target", "100",
            "--deferred", "./current.txt", "--deferred-target", "100",
        )
        self.assertEqual((code, result["status"]), (2, "error"))
        self.assertIn("more than once", result["message"])
        self.write("current.txt", "x" * 200)
        code, result = self.check(
            "--active", "current.txt", "--target", "100",
            "--deferred", "missing.txt", "--deferred-target", "100",
        )
        self.assertEqual((code, result["status"]), (2, "error"))
        self.assertNotIn("groups", result)

    def test_installed_copy_is_read_only_and_needs_no_repo_or_external_command(self):
        installed = self.root / "installed"
        installed.mkdir()
        script = installed / "check_core.py"
        shutil.copyfile(SCRIPT, script)
        self.write("current.txt", "SENSITIVE_FIXTURE_SENTINEL\n")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        code, result = self.check("--active", "current.txt", "--target", "100", script=script)
        self.assertEqual(code, 0)
        self.assertNotIn("SENSITIVE_FIXTURE_SENTINEL", json.dumps(result))
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
