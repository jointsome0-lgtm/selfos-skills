#!/usr/bin/env python3
"""Measure explicitly selected UTF-8 memory files without changing them."""

import argparse
import json
from pathlib import Path


class Parser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"status": "error", "message": message}))
        raise SystemExit(2)


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def measure(paths, target, margin, seen):
    files = []
    for name in paths:
        path = Path(name).resolve(strict=True)
        if not path.is_file():
            raise ValueError(f"Not a regular file: {name!r}")
        if path in seen:
            raise ValueError(f"File selected more than once: {name!r}")
        seen.add(path)
        try:
            size = len(path.read_bytes().decode("utf-8"))
        except UnicodeError:
            raise ValueError(f"Not a UTF-8 file: {name!r}") from None
        files.append({"path": name, "characters": size})
    total = sum(item["characters"] for item in files)
    threshold = (target * (100 + margin) + 99) // 100
    return {
        "files": files,
        "characters": total,
        "target": target,
        "review_at": threshold,
        "review_due": total >= threshold,
    }


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("--active", nargs="+", required=True, metavar="FILE")
    parser.add_argument("--target", type=positive, required=True)
    parser.add_argument("--deferred", nargs="+", metavar="FILE")
    parser.add_argument("--deferred-target", type=positive)
    parser.add_argument("--margin-percent", type=int, default=33)
    args = parser.parse_args()
    if bool(args.deferred) != (args.deferred_target is not None):
        parser.error("--deferred and --deferred-target must be used together")
    if args.margin_percent < 0:
        parser.error("--margin-percent must be nonnegative")
    seen = set()
    try:
        groups = {"active": measure(args.active, args.target, args.margin_percent, seen)}
        if args.deferred:
            groups["deferred"] = measure(args.deferred, args.deferred_target, args.margin_percent, seen)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    due = any(group["review_due"] for group in groups.values())
    print(json.dumps({"status": "review_due" if due else "ok", "groups": groups}, indent=2))
    return int(due)


if __name__ == "__main__":
    raise SystemExit(main())
