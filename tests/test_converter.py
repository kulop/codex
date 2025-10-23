from pathlib import Path

import pytest

from gaiji_converter.converter import (
    GaijiConverter,
    InteractiveFallback,
    PlaceholderFallback,
    PUAFallback,
)
from gaiji_converter.datastore import GaijiDataStore


@pytest.fixture()
def datastore(tmp_path: Path) -> GaijiDataStore:
    db_path = tmp_path / "gaiji.sqlite3"
    store = GaijiDataStore(db_path)
    schema_path = Path("db/schema.sql")
    store.initialize(schema_path)
    store.load_csv(Path("data/gaiji_mappings.csv"), source="test")
    return store


def test_dictionary_conversion(datastore: GaijiDataStore) -> None:
    converter = GaijiConverter(datastore, [PlaceholderFallback()])
    result = converter.convert_tokens(["G001", "G002", "G004"])
    assert "".join(item.replacement for item in result) == "漢国高"


def test_pua_fallback_assigns_unique_codepoints(datastore: GaijiDataStore) -> None:
    converter = GaijiConverter(datastore, [PUAFallback()])
    results = converter.convert_tokens(["UNKNOWN1", "UNKNOWN2"])
    assert results[0].replacement != results[1].replacement
    assert results[0].strategy == "pua"


def test_interactive_fallback_placeholder(datastore: GaijiDataStore) -> None:
    responses = iter(["4"])  # choose placeholder immediately

    def fake_input(prompt: str) -> str:
        return next(responses)

    fallback = InteractiveFallback(input_func=fake_input)
    converter = GaijiConverter(datastore, [fallback])
    result = converter.convert_tokens(["UNKNOWN3"])[0]
    assert result.replacement.startswith("[GAIJI:")
    assert result.strategy.startswith("interactive")
