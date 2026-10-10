"""cli.py — entry point for the file-system / CLI template."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from my_tool import hello, version_info


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="my-tool",
        description="A vibecoding-kit file-system template project.",
    )
    p.add_argument("--version", action="version", version=version_info())

    sub = p.add_subparsers(dest="cmd", required=False)

    p_hello = sub.add_parser("hello", help="print a greeting")
    p_hello.add_argument("--name", default="world", help="who to greet")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0
    if args.cmd == "hello":
        print(hello(args.name))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
