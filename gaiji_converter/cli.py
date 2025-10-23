"""Command line interface for the gaiji conversion toolkit."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

from .converter import GaijiConverter, InteractiveFallback, PlaceholderFallback, PUAFallback
from .datastore import GaijiDataStore

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gaiji conversion CLI")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("gaiji.sqlite3"),
        help="Path to the SQLite database containing gaiji_map table",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("db/schema.sql"),
        help="Schema SQL used when initializing the database",
    )
    parser.add_argument(
        "--seed",
        type=Path,
        default=Path("data/gaiji_mappings.csv"),
        help="CSV file used to seed the gaiji mapping table",
    )
    parser.add_argument(
        "--delimiter",
        default=" ",
        help="Delimiter used to split the input gaiji ID sequence",
    )
    parser.add_argument(
        "--fallback",
        choices=["placeholder", "pua", "both"],
        default="both",
        help="Fallback strategy for unknown gaiji IDs",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive resolution for missing gaiji",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="Convert gaiji IDs to Unicode")
    convert_parser.add_argument(
        "gaiji_ids",
        nargs="+",
        help="Sequence of gaiji IDs to convert",
    )

    subparsers.add_parser("init", help="Initialize the database schema")
    subparsers.add_parser("seed", help="Load seed CSV data into the database")

    return parser


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s - %(message)s")


def _build_converter(
    datastore: GaijiDataStore, fallback: str, interactive: bool
) -> GaijiConverter:
    fallback_chain: List = []
    if interactive:
        fallback_chain.append(InteractiveFallback())
    if fallback in {"pua", "both"}:
        fallback_chain.append(PUAFallback())
    if fallback in {"placeholder", "both"}:
        fallback_chain.append(PlaceholderFallback())
    return GaijiConverter(datastore, fallback_order=fallback_chain)


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    datastore = GaijiDataStore(args.database)

    if args.command == "init":
        datastore.initialize(args.schema)
        logger.info("Initialized database at %s", args.database)
        return 0

    if args.command == "seed":
        datastore.initialize(args.schema)
        datastore.load_csv(args.seed)
        logger.info("Seeded database with data from %s", args.seed)
        return 0

    if args.command == "convert":
        datastore.initialize(args.schema)
        datastore.load_csv(args.seed)
        converter = _build_converter(datastore, args.fallback, args.interactive)
        results = converter.convert_tokens(args.gaiji_ids)
        output = "".join(result.replacement for result in results)
        for result in results:
            logger.info(
                "%s -> %s (%s)",
                result.gaiji_id,
                result.replacement,
                result.strategy,
            )
        print(output)
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
