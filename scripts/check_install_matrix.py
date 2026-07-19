#!/usr/bin/env python3
"""Exercise one installation/discovery matrix case against the canonical catalog."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "scripts" / "install_smoke_matrix.json"
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SKILL_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class SmokeFailure(RuntimeError):
    """A smoke-test assertion failed."""


def load_matrix(path: Path = MATRIX_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        matrix = json.load(handle)
    cases = matrix.get("cases")
    if matrix.get("schema_version") != 1 or not isinstance(cases, list):
        raise SmokeFailure(f"{path}: unsupported or malformed matrix")
    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(ids) != len(cases) or any(not isinstance(case_id, str) for case_id in ids):
        raise SmokeFailure(f"{path}: every matrix case needs a string id")
    if len(ids) != len(set(ids)):
        raise SmokeFailure(f"{path}: matrix case ids must be unique")
    return matrix


def canonical_skill_names(root: Path = ROOT) -> set[str]:
    return {
        path.parent.name
        for path in (root / "skills").glob("*/SKILL.md")
        if path.is_file()
    }


def assert_exact_set(label: str, expected: set[str], actual: set[str], noun: str) -> None:
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    failures: list[str] = []
    if missing:
        failures.append(f"missing {noun}{'s' if len(missing) != 1 else ''}: {', '.join(missing)}")
    if unexpected:
        failures.append(
            f"unexpected {noun}{'s' if len(unexpected) != 1 else ''}: {', '.join(unexpected)}"
        )
    if failures:
        raise SmokeFailure(f"{label}: {'; '.join(failures)}")


def _tree_manifest(root: Path) -> dict[str, tuple[bytes, bool]]:
    manifest: dict[str, tuple[bytes, bool]] = {}
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise SmokeFailure(f"{root}: unexpected symlink: {path.relative_to(root)}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            manifest[relative] = (path.read_bytes(), executable)
    return manifest


def assert_skill_tree(canonical_root: Path, installed_root: Path, checkout_root: Path) -> None:
    expected_names = canonical_skill_names(checkout_root)
    actual_names = {
        path.name
        for path in installed_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    } if installed_root.is_dir() else set()
    assert_exact_set(str(installed_root), expected_names, actual_names, "skill")

    checkout_bytes = str(checkout_root.resolve()).encode()
    for skill_name in sorted(expected_names):
        expected = _tree_manifest(canonical_root / skill_name)
        actual = _tree_manifest(installed_root / skill_name)
        assert_exact_set(
            f"installed skill {skill_name}", set(expected), set(actual), "companion file"
        )
        for relative in sorted(expected):
            expected_bytes, expected_executable = expected[relative]
            actual_bytes, actual_executable = actual[relative]
            if expected_bytes != actual_bytes:
                raise SmokeFailure(f"installed skill {skill_name}: changed companion file: {relative}")
            if expected_executable != actual_executable:
                raise SmokeFailure(
                    f"installed skill {skill_name}: executable mode mismatch: {relative}"
                )
            if checkout_bytes in actual_bytes:
                raise SmokeFailure(
                    f"installed skill {skill_name}: absolute checkout path in companion file: {relative}"
                )

    composed = installed_root / "deepen" / "references" / "codebase-design" / "SKILL.md"
    helper = installed_root / "watch" / "scripts" / "codex-pr-watch.sh"
    if not composed.is_file():
        raise SmokeFailure("installed skill deepen: missing composed codebase-design/SKILL.md")
    if not helper.is_file() or not os.access(helper, os.X_OK):
        raise SmokeFailure("installed skill watch: missing executable helper codex-pr-watch.sh")


def run_command(
    command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None
) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout
    print(f"$ {' '.join(command)}")
    print(output.rstrip())
    if completed.returncode != 0:
        raise SmokeFailure(
            f"command exited {completed.returncode}: {' '.join(command)}"
        )
    return output


def _parse_catalog_output(output: str) -> set[str]:
    clean = ANSI_RE.sub("", output)
    discovered: set[str] = set()
    in_catalog = False
    for line in clean.splitlines():
        if "Available Skills" in line:
            in_catalog = True
            continue
        if in_catalog and "Use --skill" in line:
            break
        match = re.fullmatch(r"\s*│ {4}([a-z0-9]+(?:-[a-z0-9]+)*)\s*", line)
        if in_catalog and match:
            discovered.add(match.group(1))
    return discovered


def run_catalog_case(case: dict[str, Any]) -> None:
    output = run_command(
        ["npx", "--yes", case["installer"], "add", ".", "--list"],
        env={**os.environ, "DISABLE_TELEMETRY": "1", "NO_COLOR": "1"},
    )
    assert_exact_set(
        "npx catalog discovery",
        canonical_skill_names(),
        _parse_catalog_output(output),
        "skill",
    )


def run_agent_installer_case(case: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix=f"selfos-{case['agent']}-") as temporary:
        temporary_root = Path(temporary)
        home = temporary_root / "home"
        project = temporary_root / "project"
        home.mkdir()
        project.mkdir()
        environment = {
            **os.environ,
            "HOME": str(home),
            "DISABLE_TELEMETRY": "1",
            "NO_COLOR": "1",
        }
        run_command(
            [
                "npx",
                "--yes",
                case["installer"],
                "add",
                str(ROOT),
                "--skill",
                "*",
                "--agent",
                case["agent"],
                "--global",
                "--yes",
                "--copy",
            ],
            cwd=project,
            env=environment,
        )
        destination = home / case["destination"]
        assert_skill_tree(ROOT / "skills", destination, ROOT)
        print(
            f"OK: {case['agent']} installed the exact {len(canonical_skill_names())}-skill "
            f"catalog at ~/{case['destination']}"
        )


def _json_output(command: list[str], *, env: dict[str, str]) -> Any:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    print(f"$ {' '.join(command)}")
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    print(completed.stdout.rstrip())
    if completed.returncode != 0:
        raise SmokeFailure(
            f"command exited {completed.returncode}: {' '.join(command)}"
        )
    return json.loads(completed.stdout)


def run_codex_native_case() -> None:
    with tempfile.TemporaryDirectory(prefix="selfos-codex-native-") as temporary:
        codex_home = Path(temporary) / "codex-home"
        codex_home.mkdir()
        environment = {**os.environ, "CODEX_HOME": str(codex_home)}

        added = _json_output(
            ["codex", "plugin", "marketplace", "add", str(ROOT), "--json"],
            env=environment,
        )
        if added.get("marketplaceName") != "selfos":
            raise SmokeFailure("Codex marketplace discovery: missing marketplace: selfos")

        available = _json_output(
            ["codex", "plugin", "list", "--available", "--json"], env=environment
        )
        available_ids = {plugin["pluginId"] for plugin in available.get("available", [])}
        assert_exact_set(
            "Codex marketplace discovery",
            {"selfos-skills@selfos"},
            available_ids,
            "plugin",
        )

        installed = _json_output(
            ["codex", "plugin", "add", "selfos-skills@selfos", "--json"],
            env=environment,
        )
        installed_root = Path(installed["installedPath"])
        assert_skill_tree(ROOT / "skills", installed_root / "skills", ROOT)
        print(
            f"OK: Codex CLI discovered and installed the exact "
            f"{len(canonical_skill_names())}-skill native plugin"
        )


def run_claude_root_and_legacy_case() -> None:
    with tempfile.TemporaryDirectory(prefix="selfos-claude-native-") as temporary:
        config = Path(temporary) / "claude-config"
        config.mkdir()
        environment = {**os.environ, "CLAUDE_CONFIG_DIR": str(config)}
        run_command([str(ROOT / "scripts" / "check_plugin_install.sh")], env=environment)

        installed = _json_output(["claude", "plugin", "list", "--json"], env=environment)
        actual_plugin_ids = {plugin["id"] for plugin in installed}
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        expected_plugin_ids = {
            f"{plugin['name']}@{marketplace['name']}" for plugin in marketplace["plugins"]
        }
        assert_exact_set(
            "Claude marketplace install",
            expected_plugin_ids,
            actual_plugin_ids,
            "plugin",
        )

        aggregate = next(
            plugin for plugin in installed if plugin["id"] == "selfos-skills@selfos"
        )
        aggregate_root = Path(aggregate["installPath"])
        assert_skill_tree(ROOT / "skills", aggregate_root / "skills", ROOT)

        discovered_names: set[str] = set()
        checkout_bytes = str(ROOT.resolve()).encode()
        for plugin in installed:
            plugin_root = Path(plugin["installPath"])
            for skill_file in plugin_root.glob("skills/*/SKILL.md"):
                discovered_names.add(skill_file.parent.name)
                for relative, (content, _executable) in _tree_manifest(skill_file.parent).items():
                    if checkout_bytes in content:
                        raise SmokeFailure(
                            f"Claude legacy skill {skill_file.parent.name}: absolute checkout path "
                            f"in companion file: {relative}"
                        )
        assert_exact_set(
            "Claude aggregate and legacy discovery",
            canonical_skill_names(),
            discovered_names,
            "skill",
        )
        print(
            f"OK: Claude CLI installed the exact {len(expected_plugin_ids)}-plugin marketplace "
            f"and discovered the exact {len(discovered_names)}-skill canonical set"
        )


def run_case(case: dict[str, Any]) -> None:
    kind = case["kind"]
    if kind == "catalog":
        run_catalog_case(case)
    elif kind == "agent-installer":
        run_agent_installer_case(case)
    elif kind == "codex-native":
        run_codex_native_case()
    elif kind == "claude-root-and-legacy":
        run_claude_root_and_legacy_case()
    else:
        raise SmokeFailure(f"unknown matrix case kind: {kind}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--case", help="matrix case id to execute")
    selection.add_argument(
        "--github-matrix",
        action="store_true",
        help="print the configured cases as a GitHub Actions matrix",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        matrix = load_matrix()
        if args.github_matrix:
            print(json.dumps({"include": matrix["cases"]}, separators=(",", ":")))
            return 0
        matching = [case for case in matrix["cases"] if case["id"] == args.case]
        if not matching:
            raise SmokeFailure(f"unknown matrix case: {args.case}")
        run_case(matching[0])
        print(f"PASS: installation smoke case {args.case}")
        return 0
    except (SmokeFailure, KeyError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
