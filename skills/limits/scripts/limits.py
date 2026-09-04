import ast
import collections
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
LOADER_MODULES = {
    "builtins": {"__import__"},
    "importlib": {"import_module"},
    "pytest": {"importorskip"},
}
RE = {
    "marker": re.compile(
        r"^(noqa(:\s*[A-Z]+\d+(,\s*[A-Z]+\d+)*)?|type:\s*ignore(\[[a-z-]+(,\s*[a-z-]+)*\])?)$"
    ),
    "markdown": re.compile(
        r"\.(md|markdown|mdown|mkd|mdwn|mkdn|mdtext|mdx)$", re.IGNORECASE
    ),
    "test_file": re.compile(f"^{TEST}$"),
    "test_path": re.compile(r"`([^`\n]+)`"),
    "goal": re.compile(r"^\d+\. [ \t]*\S[^\n]*(?:\n[ \t]+\S[^\n]*)*", re.MULTILINE),
    "section_break": re.compile(r"^#{1,6}(?:[ \t]+|$)", re.MULTILINE),
    "map_heading": re.compile(r"^## Map$", re.MULTILINE),
    "map_line": re.compile(r"^- `([^`]+)/`: (?=.*\S).+$", re.MULTILINE),
    "fence": re.compile(
        r"^ {0,3}(?:(?P<backtick>`{3,})[^`\n]*\n.*?(?:^ {0,3}(?P=backtick)`*[ \t]*$|\Z)|(?P<tilde>~{3,})[^\n]*\n.*?(?:^ {0,3}(?P=tilde)~*[ \t]*$|\Z))",
        re.MULTILINE | re.DOTALL,
    ),
    "html_comment": re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL),
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
    counts = collections.Counter(named)
    errors = [twice % shown(t) for t, count in sorted(counts.items()) if count > 1]
    errors += [missing % shown(t) for t in sorted(set(named) - actual)]
    return errors + [extra % shown(t) for t in sorted(actual - set(named))]


def shown(value: object) -> str:
    return ascii(str(value))


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


def loader_bindings(tree: ast.AST) -> dict[str, set[str]]:
    bindings = collections.defaultdict(set)
    bindings["__import__"].add("__import__")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name if alias.asname else alias.name.partition(".")[0]
                if module in LOADER_MODULES:
                    bindings[alias.asname or module].add(module)
        elif (
            isinstance(node, ast.ImportFrom)
            and not node.level
            and node.module in LOADER_MODULES
        ):
            for alias in node.names:
                if alias.name == "*":
                    for name in LOADER_MODULES[node.module]:
                        bindings[name].add(name)
                elif alias.name in LOADER_MODULES[node.module]:
                    bindings[alias.asname or alias.name].add(alias.name)
    return bindings


def loader_reference(node: ast.AST, bindings: dict[str, set[str]]) -> set[str]:
    if isinstance(node, ast.Name):
        return bindings.get(node.id, set()) & {
            "__import__",
            "import_module",
            "importorskip",
        }
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return {
            node.attr
            for module in bindings.get(node.value.id, set())
            if node.attr in LOADER_MODULES.get(module, set())
        }
    return set()


def imported(
    node: ast.AST, bindings: dict[str, set[str]], package_relative: bool
) -> list[str]:
    if isinstance(node, ast.Import):
        return [a.name if a.asname else bare_import(a.name) for a in node.names]
    if isinstance(node, ast.ImportFrom):
        if node.level and package_relative:
            return [PACKAGE]
        return [node.module or ""]
    return [
        name
        for func in loader_reference(node.func, bindings)
        for name in dynamic_import(node, func)
    ]


def dynamic_import(node: ast.Call, func: str) -> list[str]:
    if func == "__import__":
        level = call_argument(node, 4, "level")
        if level is not None and not (
            isinstance(level, ast.Constant) and level.value == 0
        ):
            return [PACKAGE]
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
        return [PACKAGE]
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
            if name.value.startswith("."):
                return [PACKAGE]
            return [name.value]
        return [PACKAGE]
    if func == "importorskip":
        name = call_argument(node, 0, "modname")
        if isinstance(name, ast.Constant) and isinstance(name.value, str):
            return [name.value]
        return [PACKAGE]
    return []


def pytest_plugin_imports(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Assign):
        targets = node.targets
        value = node.value
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
        value = node.value
    else:
        return []
    if not any(
        isinstance(name, ast.Name)
        and isinstance(name.ctx, ast.Store)
        and name.id == "pytest_plugins"
        for target in targets
        for name in ast.walk(target)
    ):
        return []
    if isinstance(node, ast.AugAssign) or any(
        not isinstance(target, ast.Name) for target in targets
    ):
        return [PACKAGE]
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return [value.value]
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)) and all(
        isinstance(item, ast.Constant) and isinstance(item.value, str)
        for item in value.elts
    ):
        return [item.value for item in value.elts]
    return [PACKAGE]


def package_file(f: pathlib.PurePosixPath) -> bool:
    package = tuple(PACKAGE.split("."))
    return any(parent.parts[-len(package) :] == package for parent in f.parents)


def check_python(f: pathlib.PurePosixPath, text: str, is_test: bool) -> list[str]:
    errors = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        shebang = tok.start == (1, 0) and tok.string.startswith("#!")
        if (
            tok.type == tokenize.COMMENT
            and not shebang
            and not RE["marker"].match(tok.string[1:].strip())
        ):
            errors.append(f"comment: {shown(f)}:{tok.start[0]}")
    tree = ast.parse(text)
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    bindings = loader_bindings(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            errors.append(f"docstring: {shown(f)}:{node.lineno}")
        if (
            is_test
            and isinstance(node, (ast.Name, ast.Attribute))
            and isinstance(node.ctx, ast.Load)
            and loader_reference(node, bindings)
            and not (
                isinstance(parents.get(node), ast.Call) and parents[node].func is node
            )
        ):
            errors.append(f"test loader reference: {shown(f)}:{node.lineno}")
        if is_test and isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
                ast.Call,
                ast.Assign,
                ast.AnnAssign,
                ast.AugAssign,
            ),
        ):
            names = (
                imported(node, bindings, package_file(f))
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Call))
                else pytest_plugin_imports(node)
            )
            bad = [
                n
                for n in names
                if (n == PACKAGE or n.startswith(f"{PACKAGE}."))
                and (n != TESTING or getattr(node, "level", 0))
            ]
            errors += [f"test import: {shown(f)}:{node.lineno} {shown(n)}" for n in bad]
    return errors


def has_test_definition(text: str) -> bool:
    body = ast.parse(text).body
    definitions = [*body]
    for node in body:
        if isinstance(node, ast.ClassDef):
            definitions.extend(node.body)
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
        for node in definitions
    )


def read_python(f: pathlib.PurePosixPath) -> str:
    with tokenize.open(ROOT / f) as source:
        return source.read()


def markdown(text: str) -> str:
    return RE["html_comment"].sub("", RE["fence"].sub("", text))


def check_map(dirs: set[str], text: str) -> list[str]:
    text = markdown(text)
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
        [f"{d}/" for d, _ in lines],
        {f"{d}/" for d in dirs},
        "map: duplicate line for %s",
        "map: no directory %s",
        "map: no line for %s",
    )
    return errors + [
        f"map: line for {shown(f'{d}/')} exceeds {MAP_LINE_CHARS} chars"
        for d, line in lines
        if len(line) > MAP_LINE_CHARS
    ]


def check_goals(tests: set[str], text: str) -> list[str]:
    named, errors = [], []
    for entry in RE["goal"].findall(markdown(text)):
        paths = [
            path
            for path in RE["test_path"].findall(entry)
            if RE["test_file"].fullmatch(path)
        ]
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
        str(p) for f in index for p in f.parents if p != pathlib.PurePosixPath(".")
    } | links
    counted = [
        f
        for f in index
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
    errors += [f"symlink: {shown(f)}" for f in sorted(symlinks)]
    tracked = {str(f) for f in index}
    required = {"README.md", "GOALS.md"}
    errors += [
        f"required file: {shown(f)} is missing" for f in sorted(required - tracked)
    ]
    errors += [
        f"required file: {shown(f)} is a submodule" for f in sorted(required & links)
    ]
    errors += [
        f"artifact: {shown(f)}"
        for f in index
        if str(f) not in links
        and RE["markdown"].search(str(f))
        and str(f) not in ALLOWED_MARKDOWN
    ]
    blocked = links | symlinks
    regular = tracked - blocked
    python = {
        f: read_python(f)
        for f in index
        if str(f) not in blocked and f.suffix.lower() in (".py", ".pyi", ".pyw")
    }
    for f, text in python.items():
        errors += check_python(
            f,
            text,
            "tests" in f.parts[:-1]
            or bool(RE["test_file"].match(str(f)))
            or f.name == "conftest.py",
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
        test_files = {str(f) for f in python if RE["test_file"].match(str(f))}
        errors += [
            f"test: {shown(f)} defines no test"
            for f in sorted(test_files)
            if not has_test_definition(python[pathlib.PurePosixPath(f)])
        ]
        errors += check_goals(
            test_files,
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
