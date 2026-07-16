#!/usr/bin/env python3
"""Self-test for sync_conventions.py against invented consuming repositories."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPTS_DIR / "sync_conventions.py"
TEMPLATE = SCRIPTS_DIR.parent / "conventions" / "SDD-CONVENTIONS.md"

# Editing the template requires bumping these pins in the same change — that
# is the intended drift detection, not an inconvenience: a body edit without
# a version bump must fail CI here instead of drifting silently.
PINNED_VERSION = "1.0.0"
PINNED_DIGEST = "30cba528aee9a6ebbb08c24739d0269bb12768fd368043ce2b63e73f1480bfda"

ATLAS_PREAMBLE = (
    "# atlas — agent guide\n"
    "\n"
    "Invented fixture repository. Local lanes: Track A ships, Track B learns.\n"
)
LOCAL_ADDENDUM = (
    "\n"
    "## atlas-specific rules\n"
    "\n"
    "- Invented local rule that must survive regeneration.\n"
)


def run(*argv: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *map(str, argv)], capture_output=True, text=True, cwd=cwd
    )


def bumped_template(directory: Path) -> Path:
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    lines[0] = "<!-- sdd-conventions-template v1.1.0 -->"
    lines.append("- **Invented extra rule.** Added by the fixture to model an update.")
    path = directory / "SDD-CONVENTIONS.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class SyncConventionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="sdd-conventions-test."))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)

    def agents_file(self, name: str = "atlas") -> Path:
        path = self.directory / name / "AGENTS.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ATLAS_PREAMBLE.replace("atlas", name), encoding="utf-8")
        return path

    def test_sync_inserts_block_and_check_passes(self) -> None:
        target = self.agents_file()
        sync = run(SCRIPT, "sync", target)
        self.assertEqual(sync.returncode, 0, sync.stderr)
        content = target.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(ATLAS_PREAMBLE))
        self.assertIn("<!-- BEGIN SDD-CONVENTIONS v1.0.0 sha256:", content)

        check = run(SCRIPT, "check", target)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("matches template v1.0.0", check.stdout)

    def test_sync_is_idempotent_and_preserves_local_content(self) -> None:
        target = self.agents_file()
        run(SCRIPT, "sync", target)
        target.write_text(target.read_text(encoding="utf-8") + LOCAL_ADDENDUM, encoding="utf-8")

        again = run(SCRIPT, "sync", target)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("already up to date", again.stdout)
        content = target.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(ATLAS_PREAMBLE))
        self.assertTrue(content.endswith(LOCAL_ADDENDUM))
        self.assertEqual(run(SCRIPT, "check", target).returncode, 0)

    def test_check_detects_stale_after_template_update(self) -> None:
        target = self.agents_file("exp2res")
        run(SCRIPT, "sync", target)
        updated_template = bumped_template(self.directory)

        check = run(SCRIPT, "check", target, "--template", updated_template)
        self.assertEqual(check.returncode, 1)
        self.assertIn("stale against template v1.1.0", check.stderr)

    def test_sync_applies_template_update_preserving_content(self) -> None:
        target = self.agents_file()
        run(SCRIPT, "sync", target)
        target.write_text(target.read_text(encoding="utf-8") + LOCAL_ADDENDUM, encoding="utf-8")
        updated_template = bumped_template(self.directory)

        sync = run(SCRIPT, "sync", target, "--template", updated_template)
        self.assertEqual(sync.returncode, 0, sync.stderr)
        self.assertIn("Updated", sync.stdout)
        content = target.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(ATLAS_PREAMBLE))
        self.assertTrue(content.endswith(LOCAL_ADDENDUM))
        self.assertIn("Invented extra rule", content)

        check = run(SCRIPT, "check", target, "--template", updated_template)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_sync_preserves_crlf_outside_block(self) -> None:
        target = self.agents_file()
        crlf_preamble = ATLAS_PREAMBLE.replace("\n", "\r\n")
        target.write_bytes(crlf_preamble.encode("utf-8"))

        sync = run(SCRIPT, "sync", target)
        self.assertEqual(sync.returncode, 0, sync.stderr)
        raw = target.read_bytes().decode("utf-8")
        self.assertTrue(raw.startswith(crlf_preamble))

        crlf_addendum = LOCAL_ADDENDUM.replace("\n", "\r\n")
        target.write_bytes((raw + crlf_addendum).encode("utf-8"))
        updated_template = bumped_template(self.directory)

        refresh = run(SCRIPT, "sync", target, "--template", updated_template)
        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        raw = target.read_bytes().decode("utf-8")
        self.assertTrue(raw.startswith(crlf_preamble))
        self.assertTrue(raw.endswith(crlf_addendum))
        self.assertIn("Invented extra rule", raw)

        again = run(SCRIPT, "sync", target, "--template", updated_template)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("already up to date", again.stdout)
        check = run(SCRIPT, "check", target, "--template", updated_template)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_check_detects_tampered_block(self) -> None:
        target = self.agents_file()
        run(SCRIPT, "sync", target)
        tampered = target.read_text(encoding="utf-8").replace(
            "Stable section numbers", "Renumber sections freely"
        )
        target.write_text(tampered, encoding="utf-8")

        check = run(SCRIPT, "check", target)
        self.assertEqual(check.returncode, 1)
        self.assertIn("does not match its recorded sha256", check.stderr)

    def test_vendored_copy_checks_offline(self) -> None:
        repo = self.directory / "exp2res"
        vendored = repo / "scripts" / "check_sdd_conventions.py"
        vendored.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SCRIPT, vendored)
        target = self.agents_file("exp2res")
        run(SCRIPT, "sync", target)

        check = run(vendored, "check", "AGENTS.md", cwd=repo)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("local check only; no template available", check.stdout)

    def test_vendored_sync_requires_template(self) -> None:
        repo = self.directory / "exp2res"
        vendored = repo / "scripts" / "check_sdd_conventions.py"
        vendored.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SCRIPT, vendored)

        sync = run(vendored, "sync", "AGENTS.md", cwd=repo)
        self.assertEqual(sync.returncode, 1)
        self.assertIn("sync requires a template", sync.stderr)

    def test_malformed_markers_are_refused(self) -> None:
        fake_begin = "<!-- BEGIN SDD-CONVENTIONS v1.0.0 sha256:" + "0" * 64 + " -->"
        duplicated = self.directory / "duplicated.md"
        duplicated.write_text(
            f"{fake_begin}\nbody\n<!-- END SDD-CONVENTIONS -->\n{fake_begin}\n",
            encoding="utf-8",
        )
        check = run(SCRIPT, "check", duplicated)
        self.assertEqual(check.returncode, 1)
        self.assertIn("multiple SDD-CONVENTIONS markers", check.stderr)

        unpaired = self.directory / "unpaired.md"
        unpaired.write_text(f"preamble\n{fake_begin}\nbody\n", encoding="utf-8")
        for command in ("check", "sync"):
            result = run(SCRIPT, command, unpaired)
            self.assertEqual(result.returncode, 1, f"{command}: {result.stdout}")
            self.assertIn("unpaired or out of order", result.stderr)

    def test_sync_creates_missing_target(self) -> None:
        target = self.directory / "fresh" / "AGENTS.md"
        target.parent.mkdir(parents=True)
        sync = run(SCRIPT, "sync", target)
        self.assertEqual(sync.returncode, 0, sync.stderr)
        self.assertIn("Created", sync.stdout)
        self.assertEqual(run(SCRIPT, "check", target).returncode, 0)

    def test_check_names_missing_block(self) -> None:
        target = self.agents_file()
        check = run(SCRIPT, "check", target)
        self.assertEqual(check.returncode, 1)
        self.assertIn("no SDD-CONVENTIONS block found", check.stderr)

    def test_template_is_pinned(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            from sync_conventions import body_digest, load_template
        finally:
            sys.path.pop(0)
        version, body = load_template(TEMPLATE)
        self.assertEqual(version, PINNED_VERSION)
        self.assertEqual(body_digest(body), PINNED_DIGEST)


if __name__ == "__main__":
    unittest.main()
