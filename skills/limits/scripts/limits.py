import ast
import io
import os
import pathlib
import re
import subprocess
import sys
import tokenize

ROOT = pathlib.Path(
    os.fsdecode(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, check=True
        ).stdout.removesuffix(b"\n")
    )
)
PACKAGE = sys.argv[1] if len(sys.argv) > 1 else ""
TESTING = f"{PACKAGE}.testing"
BUDGET_TOKENS = int(sys.argv[2]) if len(sys.argv) > 2 else 70_000
MAP_LINE_CHARS = 250
ALLOWED_MARKDOWN = {"GOALS.md", "AGENTS.md", "README.md", "CLAUDE.md"}
LOCKS = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "uv.lock",
}
TEST_NAME = r"(?:test_[^/]*|[^/]*_test)\.py"
TEST = rf"(?:[^/.][^/]*/)*{TEST_NAME}"
MARKDOWN_INDENT = r" {0,3}"
LIST_MARKER = rf"{MARKDOWN_INDENT}(?:\d{{1,9}}[.)]|[-+*])[ \t]+"
ATX_HEADING = rf"{MARKDOWN_INDENT}#{{1,6}}(?:[ \t]+|$)"
SETEXT_HEADING = rf"(?!{LIST_MARKER}|{ATX_HEADING}|{MARKDOWN_INDENT}>).+\n{MARKDOWN_INDENT}(?:=+|-+)[ \t]*$"
HEADING = rf"(?:{ATX_HEADING}|{SETEXT_HEADING})"
THEMATIC_BREAK = (
    rf"{MARKDOWN_INDENT}(?:(?:\*[ \t]*){{3,}}|(?:-[ \t]*){{3,}}|(?:_[ \t]*){{3,}})$"
)
RE = {
    "marker": re.compile(
        r"^(noqa(:\s*[A-Z]+\d+(,\s*[A-Z]+\d+)*)?|type:\s*ignore(\[[a-z-]+(,\s*[a-z-]+)*\])?)$"
    ),
    "markdown": re.compile(
        r"\.(md|markdown|mdown|mkd|mdwn|mkdn|mdtext|mdx)$", re.IGNORECASE
    ),
    "test_file": re.compile(f"^{TEST}$"),
    "test_path": re.compile(f"`({TEST})`"),
    "goal_start": re.compile(r"^( {0,3})(\d{1,9}[.)])([ \t]+).+"),
    "list_start": re.compile(r"^( *)(?:\d{1,9}[.)]|[-+*])[ \t]+"),
    "atx_heading": re.compile(r"^( *)#{1,6}(?:[ \t]+|$)"),
    "setext_underline": re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$"),
    "thematic_break": re.compile(rf"^{THEMATIC_BREAK}"),
    "section_break": re.compile(rf"^(?:{HEADING}|{THEMATIC_BREAK})", re.MULTILINE),
    "map_heading": re.compile(r"^## Map$", re.MULTILINE),
    "map_line": re.compile(r"^- `([^`]+)/`: (?=.*\S).+$", re.MULTILINE),
    "fence": re.compile(
        r"^ {0,3}(`{3,}|~{3,}).*?(?:^ {0,3}\1[`~ \t]*$|\Z)", re.MULTILINE | re.DOTALL
    ),
    "html_comment": re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL),
    "package": re.compile(rf"^{re.escape(PACKAGE)}(\.\w+)*$"),
}


def git(*args: str) -> list[str]:
    return (
        subprocess.run(["git", *args, "-z"], cwd=ROOT, capture_output=True, check=True)
        .stdout.decode(errors="surrogateescape")
        .split("\0")
    )


def blob_sizes(objects: list[str]) -> list[int]:
    if not objects:
        return []
    return [
        int(size)
        for size in subprocess.run(
            ["git", "cat-file", "--batch-check=%(objectsize)"],
            cwd=ROOT,
            input="".join(f"{object_id}\n" for object_id in objects),
            capture_output=True,
            check=True,
            text=True,
        )
        .stdout.strip()
        .splitlines()
    ]


def compare(
    named: list[str], actual: set[str], twice: str, missing: str, extra: str
) -> list[str]:
    errors = [twice % t for t in sorted({t for t in named if named.count(t) > 1})]
    errors += [missing % t for t in sorted(set(named) - actual)]
    return errors + [extra % t for t in sorted(actual - set(named))]


def call_argument(node: ast.Call, position: int, keyword: str) -> ast.AST | None:
    if len(node.args) > position:
        return node.args[position]
    return next((item.value for item in node.keywords if item.arg == keyword), None)


def bare_import(name: str) -> str:
    if name == PACKAGE or name.startswith(f"{PACKAGE}."):
        return PACKAGE
    return name.partition(".")[0]


def resolve_import(name: str, package: str) -> str:
    level = len(name) - len(name.lstrip("."))
    if not level:
        return name
    parents = package.split(".")
    if level > len(parents):
        return name
    base = ".".join(parents[: len(parents) - level + 1])
    tail = name[level:]
    return f"{base}.{tail}" if tail else base


def imported(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [a.name if a.asname else bare_import(a.name) for a in node.names]
    if isinstance(node, ast.ImportFrom):
        return [node.module or ""]
    func = (
        node.func.attr
        if isinstance(node.func, ast.Attribute)
        else getattr(node.func, "id", "")
    )
    if func == "__import__":
        name = call_argument(node, 0, "name")
        fromlist = call_argument(node, 3, "fromlist")
        if isinstance(name, ast.Constant) and isinstance(name.value, str):
            nonempty = (
                isinstance(fromlist, ast.Constant)
                and bool(fromlist.value)
                or isinstance(fromlist, (ast.List, ast.Tuple, ast.Set))
                and bool(fromlist.elts)
                or isinstance(fromlist, ast.Dict)
                and bool(fromlist.keys)
            )
            return [name.value if nonempty else bare_import(name.value)]
        return []
    if func == "import_module":
        name = call_argument(node, 0, "name")
        package = call_argument(node, 1, "package")
        if isinstance(name, ast.Constant) and isinstance(name.value, str):
            if (
                name.value.startswith(".")
                and isinstance(package, ast.Constant)
                and isinstance(package.value, str)
            ):
                return [resolve_import(name.value, package.value)]
            return [name.value]
        return []
    if func == "importorskip":
        name = call_argument(node, 0, "modname")
        if isinstance(name, ast.Constant) and isinstance(name.value, str):
            return [name.value]
    return []


def check_python(f: pathlib.Path, text: str, is_test: bool) -> list[str]:
    errors = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        shebang = tok.start == (1, 0) and tok.string.startswith("#!")
        if (
            tok.type == tokenize.COMMENT
            and not shebang
            and not RE["marker"].match(tok.string[1:].strip())
        ):
            errors.append(f"comment: {f}:{tok.start[0]}")
    for node in ast.walk(ast.parse(text)):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            errors.append(f"docstring: {f}:{node.lineno}")
        if is_test and isinstance(node, (ast.Import, ast.ImportFrom, ast.Call)):
            names = imported(node)
            bad = [
                n
                for n in names
                if RE["package"].match(n)
                and (n != TESTING or getattr(node, "level", 0))
            ]
            errors += [f"test import: {f}:{node.lineno} {n}" for n in bad]
    return errors


def has_test(text: str) -> bool:
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
        for node in ast.walk(ast.parse(text))
    )


def read_python(f: pathlib.PurePosixPath) -> str:
    with tokenize.open(ROOT / f) as source:
        return source.read()


def goal_entries(text: str) -> list[str]:
    lines = text.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        match = RE["goal_start"].match(lines[i])
        if not match:
            i += 1
            continue
        content_indent = len(match[1]) + len(match[2]) + len(match[3].expandtabs(4))
        entry = [lines[i]]
        i += 1
        while i < len(lines):
            raw = lines[i]
            if not raw.strip():
                following = i
                while following < len(lines) and not lines[following].strip():
                    following += 1
                if following < len(lines):
                    indent = len(lines[following]) - len(lines[following].lstrip(" "))
                    if indent >= content_indent:
                        entry.extend(lines[i:following])
                        i = following
                        continue
                break
            indent = len(raw) - len(raw.lstrip(" "))
            marker = RE["list_start"].match(raw)
            heading = RE["atx_heading"].match(raw)
            setext = i + 1 < len(lines) and RE["setext_underline"].match(lines[i + 1])
            if (
                (marker and len(marker[1]) < content_indent)
                or (heading and len(heading[1]) < content_indent)
                or (setext and indent < content_indent and not marker)
                or (RE["thematic_break"].match(raw) and indent < content_indent)
                or (raw.lstrip().startswith(">") and indent < content_indent)
            ):
                break
            entry.append(raw)
            i += 1
        entries.append("\n".join(entry))
    return entries


def check_map(dirs: set[str], text: str) -> list[str]:
    text = RE["fence"].sub("", text)
    text = RE["html_comment"].sub("", text)
    match = RE["map_heading"].search(text)
    section = RE["section_break"].split(text[match.end() :], 1)[0] if match else ""
    lines = [(m[1], m[0]) for m in RE["map_line"].finditer(section)]
    raws = section.splitlines()
    errors = [] if match else ["map: no ## Map heading in README.md"]
    errors += [
        f"map: wrapped line {i}"
        for i, raw in enumerate(raws, 1)
        if raw.strip() and (raw.startswith(" ") or not RE["map_line"].match(raw))
    ]
    errors += compare(
        [d for d, _ in lines],
        dirs,
        "map: duplicate line for %s/",
        "map: no directory %s/",
        "map: no line for %s/",
    )
    return errors + [
        f"map: line for {d}/ exceeds {MAP_LINE_CHARS} chars"
        for d, line in lines
        if len(line) > MAP_LINE_CHARS
    ]


def check_goals(tests: set[str], text: str) -> list[str]:
    named, errors = [], []
    for entry in goal_entries(RE["html_comment"].sub("", RE["fence"].sub("", text))):
        paths = RE["test_path"].findall(entry)
        if len(paths) != 1:
            number = entry.lstrip().split(maxsplit=1)[0].rstrip(".)")
            errors.append(f"goals: entry {number} names {len(paths)} tests")
        named += paths
    return errors + compare(
        named,
        tests,
        "goals: %s named twice",
        "goals: %s named in GOALS.md but missing",
        "goals: %s exists but no goal names it",
    )


def main() -> int:
    if not PACKAGE:
        print("usage: python limits.py <package> [budget-tokens]")
        return 2
    files = [pathlib.PurePosixPath(p) for p in git("ls-files") if p]
    entries = git("ls-files", "-s")
    index = {}
    for entry in entries:
        if entry:
            meta, path = entry.split("\t", 1)
            mode, object_id, _ = meta.split()
            index[pathlib.PurePosixPath(path)] = (mode, object_id)
    links = {str(path) for path, item in index.items() if item[0] == "160000"}
    symlinks = {str(path) for path, item in index.items() if item[0] == "120000"}
    dirs = {
        str(p) for f in files for p in f.parents if p != pathlib.PurePosixPath(".")
    } | links
    counted = [
        f
        for f in files
        if str(f) not in links | {"LICENSE"}
        and f.name not in LOCKS
        and f.suffix != ".lock"
    ]
    tokens = (sum(blob_sizes([index[f][1] for f in counted])) + 3) // 4
    errors = (
        []
        if tokens <= BUDGET_TOKENS
        else [f"budget: {tokens} tokens, limit {BUDGET_TOKENS}"]
    )
    errors += [f"symlink: {f}" for f in sorted(symlinks)]
    tracked = {str(f) for f in files}
    required = {"README.md", "GOALS.md"}
    errors += [f"required file: {f} is missing" for f in sorted(required - tracked)]
    errors += [f"required file: {f} is a submodule" for f in sorted(required & links)]
    errors += [
        f"artifact: {f}"
        for f in files
        if str(f) not in links
        and RE["markdown"].search(str(f))
        and str(f) not in ALLOWED_MARKDOWN
    ]
    blocked = links | symlinks
    regular = tracked - blocked
    python = {
        f: read_python(f)
        for f in files
        if str(f) not in blocked and f.suffix.lower() in (".py", ".pyi", ".pyw")
    }
    for f, text in python.items():
        errors += check_python(
            f,
            text,
            bool(RE["test_file"].match(str(f))) or f.name == "conftest.py",
        )
    if "README.md" in regular:
        errors += check_map(
            {
                d
                for d in dirs
                if not any(
                    part.startswith(".") for part in pathlib.PurePosixPath(d).parts
                )
            },
            (ROOT / "README.md").read_text(encoding="utf-8"),
        )
    if "GOALS.md" in regular:
        errors += check_goals(
            {
                str(f)
                for f, text in python.items()
                if RE["test_file"].match(str(f)) and has_test(text)
            },
            (ROOT / "GOALS.md").read_text(encoding="utf-8"),
        )
    print(
        *errors,
        f"budget: {tokens} of {BUDGET_TOKENS} tokens",
        f"limits: {len(errors)} problems",
        sep="\n",
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
