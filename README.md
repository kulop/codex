# Gaiji Conversion Prototype

This repository provides a prototype workflow for researching external character (外字) resources,
managing mappings in SQLite, converting gaiji identifiers to Unicode, and evaluating the results.

## Project Layout
- `docs/GAIJI_RESOURCES.md`: Summary of existing gaiji code sets, fonts, and conversion tables.
- `data/gaiji_mappings.csv`: Seed dictionary mapping gaiji IDs to Unicode characters and metadata.
- `db/schema.sql`: SQLite schema defining the `gaiji_map` table and update trigger.
- `gaiji_converter/`: Python package containing the datastore, conversion engine, and CLI entry point.
- `scripts/evaluate_accuracy.py`: Utility for measuring conversion accuracy against reference documents.
- `tests/`: Pytest-based regression tests and sample corpora for evaluation.
- `web/app.py`: Minimal Flask app for browsing mappings and running conversions in a browser.

## Quick Start
1. **Initialize and seed the database**
   ```bash
   python -m gaiji_converter.cli --database gaiji.sqlite3 init
   python -m gaiji_converter.cli --database gaiji.sqlite3 seed
   ```

2. **Convert gaiji IDs to Unicode**
   ```bash
   python -m gaiji_converter.cli --database gaiji.sqlite3 convert G001 G002 G003 G999
   ```
   Unknown gaiji IDs fall back to either PUA assignments or human-in-the-loop prompts depending on
   CLI options (`--fallback` and `--interactive`).

3. **Evaluate conversion accuracy**
   ```bash
   python scripts/evaluate_accuracy.py --fallback placeholder \
       tests/sample_document.txt tests/sample_expected.txt
   ```

## Testing
Install the optional development dependencies and run the test suite:

```bash
pip install -e .[dev]
pytest
```

## Future Work
- Expand the seed mapping by ingesting MJ/IPA/Adobe-Japan1 resources.
- Attach glyph previews (SVG/bitmap) for Web UI review flows.
- Build a lightweight web dashboard that lets operators edit mappings and approve conversions.
