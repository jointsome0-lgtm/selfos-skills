import ast
import io
import pathlib
import re
import subprocess
import sys
import tokenize

ROOT = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, check=True).stdout.decode().strip())
PACKAGE = sys.argv[1] if len(sys.argv) > 1 else ""
TESTING = f"{PACKAGE}.testing"
BUDGET_TOKENS = int(sys.argv[2]) if len(sys.argv) > 2 else 70_000
MAP_LINE_CHARS = 250
ALLOWED_MARKDOWN = {"GOALS.md", "AGENTS.md", "README.md", "CLAUDE.md"}
LOCKS = {"package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "poetry.lock", "uv.lock"}
TEST = r"tests/(?:[^/.][^/]*/)*(?:test_[^/]*|[^/]*_test)\.py"
RE = {
    "marker": re.compile(r"^(noqa(:\s*[A-Z]+\d+(,\s*[A-Z]+\d+)*)?|type:\s*ignore(\[[a-z-]+(,\s*[a-z-]+)*\])?)$"),
    "markdown": re.compile(r"\.(md|markdown|mdown|mkd|mdwn|mkdn|mdtext|mdx)$", re.IGNORECASE),
    "test_file": re.compile(f"^{TEST}$"),
    "test_path": re.compile(f"`({TEST})`"),
    "test_def": re.compile(r"^\s*(?:async )?def test\w*\(", re.MULTILINE),
    "goal": re.compile(r"^\d+\. (?:.+(?:\n|\Z))+?(?=\n|^\d+\. |\Z)", re.MULTILINE),
    "heading": re.compile(r"^#{1,6} ", re.MULTILINE),
    "map_heading": re.compile(r"^## Map$", re.MULTILINE),
    "map_line": re.compile(r"^- `([^`]+)/`: .+$", re.MULTILINE),
    "fence": re.compile(r"^```.*?(?:^```$|\Z)", re.MULTILINE | re.DOTALL),
    "package": re.compile(rf"^{re.escape(PACKAGE)}(\.\w+)*$"),
}


def git(*args: str) -> list[str]:
    return subprocess.run(["git", *args, "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode(errors="surrogateescape").split("\0")


def compare(named: list[str], actual: set[str], twice: str, missing: str, extra: str) -> list[str]:
    errors = [twice % t for t in sorted({t for t in named if named.count(t) > 1})]
    errors += [missing % t for t in sorted(set(named) - actual)]
    return errors + [extra % t for t in sorted(actual - set(named))]


def imported(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [a.name if a.asname else a.name.partition(".")[0] for a in node.names]
    if isinstance(node, ast.ImportFrom):
        return [node.module or ""]
    func = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
    args = [*node.args, *(k.value for k in node.keywords)] if func in ("import_module", "__import__", "importorskip") else []
    return [a.value for a in args if isinstance(a, ast.Constant) and isinstance(a.value, str)]


def check_python(f: pathlib.Path, text: str, is_test: bool) -> list[str]:
    errors = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        shebang = tok.start == (1, 0) and tok.string.startswith("#!")
        if tok.type == tokenize.COMMENT and not shebang and not RE["marker"].match(tok.string[1:].strip()):
            errors.append(f"comment: {f}:{tok.start[0]}")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            errors.append(f"docstring: {f}:{node.lineno}")
        if is_test and isinstance(node, (ast.Import, ast.ImportFrom, ast.Call)):
            names = imported(node)
            bad = [n for n in names if RE["package"].match(n) and (n != TESTING or getattr(node, "level", 0))]
            errors += [f"test import: {f}:{node.lineno} {n}" for n in bad]
    return errors


def check_map(dirs: set[str]) -> list[str]:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    match = RE["map_heading"].search(text)
    section = RE["heading"].split(text[match.end():], 1)[0] if match else ""
    lines = [(m[1], m[0]) for m in RE["map_line"].finditer(section)]
    raws = section.splitlines()
    start = next((i for i, raw in enumerate(raws, 1) if raw.startswith("- ")), len(raws))
    errors = [] if match else ["map: no ## Map heading in README.md"]
    errors += [f"map: wrapped line {i}" for i, raw in enumerate(raws, 1) if raw.strip() and (raw.startswith(" ") or (i > start and not RE["map_line"].match(raw)))]
    errors += compare([d for d, _ in lines], dirs, "map: duplicate line for %s/", "map: no directory %s/", "map: no line for %s/")
    return errors + [f"map: line for {d}/ exceeds {MAP_LINE_CHARS} chars" for d, line in lines if len(line) > MAP_LINE_CHARS]


def check_goals(tests: set[str]) -> list[str]:
    named, errors = [], []
    for entry in RE["goal"].findall(RE["fence"].sub("", (ROOT / "GOALS.md").read_text(encoding="utf-8"))):
        paths = RE["test_path"].findall(entry)
        if len(paths) != 1:
            errors.append(f"goals: entry {entry.split('.')[0]} names {len(paths)} tests")
        named += paths
    return errors + compare(named, tests, "goals: %s named twice", "goals: %s named in GOALS.md but missing", "goals: %s exists but no goal names it")


def main() -> int:
    if not PACKAGE:
        print("usage: python limits.py <package> [budget-tokens]")
        return 2
    files = [pathlib.PurePosixPath(p) for p in git("ls-files") if p]
    entries = git("ls-files", "-s")
    links = {e.split("\t", 1)[1] for e in entries if e.startswith("160000 ")}
    symlinks = {e.split("\t", 1)[1] for e in entries if e.startswith("120000 ")}
    dirs = {str(p) for f in files for p in f.parents if p != pathlib.PurePosixPath(".")} | links
    counted = [f for f in files if str(f) not in links | {"LICENSE"} and f.name not in LOCKS and f.suffix != ".lock"]
    tokens = (sum((ROOT / f).lstat().st_size for f in counted) + 3) // 4
    errors = [] if tokens <= BUDGET_TOKENS else [f"budget: {tokens} tokens, limit {BUDGET_TOKENS}"]
    errors += [f"symlink: {f}" for f in sorted(symlinks)]
    errors += [f"artifact: {f}" for f in files if RE["markdown"].search(str(f)) and str(f) not in ALLOWED_MARKDOWN]
    for f in files:
        if str(f) not in symlinks and f.suffix.lower() in (".py", ".pyi", ".pyw"):
            errors += check_python(f, (ROOT / f).read_text(encoding="utf-8"), f.parts[0] == "tests" or f.name == "conftest.py")
    errors += check_map({d for d in dirs if not any(part.startswith(".") for part in pathlib.PurePosixPath(d).parts)})
    errors += check_goals({str(f) for f in files if str(f) not in symlinks and RE["test_file"].match(str(f)) and RE["test_def"].search((ROOT / f).read_text(encoding="utf-8"))})
    print(*errors, f"budget: {tokens} of {BUDGET_TOKENS} tokens", f"limits: {len(errors)} problems", sep="\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
