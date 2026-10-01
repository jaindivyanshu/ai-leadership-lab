"""CLI: python -m scorecard examples/*.json [-o report.md] [--json]"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from . import UseCase, ValidationError, render_portfolio, score


def load(path: Path) -> list[UseCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else [raw]
    return [UseCase.from_dict(item) for item in items]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="scorecard", description=__doc__)
    p.add_argument("files", nargs="+", type=Path, help="JSON use-case file(s)")
    p.add_argument("-o", "--output", type=Path, help="write Markdown report here (default: stdout)")
    p.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = p.parse_args(argv)

    try:
        cases = [uc for f in args.files for uc in load(f)]
    except (ValidationError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    results = [score(uc) for uc in cases]
    if args.json:
        out = json.dumps([dataclasses.asdict(r) for r in results], indent=2)
    else:
        out = render_portfolio(results)

    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"wrote {args.output} ({len(results)} use cases)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
