"""Evaluate conversion accuracy against expected outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gaiji_converter.cli import _build_converter, configure_logging
from gaiji_converter.datastore import GaijiDataStore


def evaluate(document: Path, expected: Path, delimiter: str, fallback: str, interactive: bool) -> float:
    datastore = GaijiDataStore(Path("gaiji_eval.sqlite3"))
    datastore.initialize(Path("db/schema.sql"))
    datastore.load_csv(Path("data/gaiji_mappings.csv"))
    converter = _build_converter(datastore, fallback, interactive)

    tokens = document.read_text(encoding="utf-8").strip().split(delimiter)
    expected_tokens = expected.read_text(encoding="utf-8").strip().split(delimiter)
    results = converter.convert_tokens(tokens)

    correct = 0
    for result, expected_token in zip(results, expected_tokens):
        if result.replacement == expected_token:
            correct += 1
    accuracy = correct / len(tokens) if tokens else 0.0
    return accuracy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate gaiji conversion accuracy")
    parser.add_argument("document", type=Path)
    parser.add_argument("expected", type=Path)
    parser.add_argument("--delimiter", default=" ")
    parser.add_argument("--fallback", choices=["placeholder", "pua", "both"], default="both")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    configure_logging(args.verbose)

    accuracy = evaluate(args.document, args.expected, args.delimiter, args.fallback, args.interactive)
    print(f"Accuracy: {accuracy:.2%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
