"""SQLite-backed datastore for gaiji mappings."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


@dataclass
class GaijiEntry:
    """Data class representing a gaiji mapping entry."""

    gaiji_id: str
    unicode_codepoint: Optional[str]
    character: Optional[str]
    reading: Optional[str]
    radical: Optional[str]
    stroke_count: Optional[int]
    pua_codepoint: Optional[str]
    source: Optional[str]
    notes: Optional[str]


class GaijiDataStore:
    """Helper class that manages SQLite persistence for gaiji mappings."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._connection: Optional[sqlite3.Connection] = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.database_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def initialize(self, schema_path: Path) -> None:
        with schema_path.open("r", encoding="utf-8") as fh:
            schema_sql = fh.read()
        self.connection.executescript(schema_sql)
        self.connection.commit()

    def load_csv(self, csv_path: Path, source: str | None = None) -> None:
        with csv_path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = [self._normalize_row(row, source) for row in reader]
        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO gaiji_map (
                    gaiji_id,
                    unicode_codepoint,
                    character,
                    reading,
                    radical,
                    stroke_count,
                    pua_codepoint,
                    source,
                    notes
                ) VALUES (:gaiji_id, :unicode_codepoint, :character, :reading, :radical,
                         :stroke_count, :pua_codepoint, :source, :notes)
                ON CONFLICT(gaiji_id) DO UPDATE SET
                    unicode_codepoint = excluded.unicode_codepoint,
                    character = excluded.character,
                    reading = excluded.reading,
                    radical = excluded.radical,
                    stroke_count = excluded.stroke_count,
                    pua_codepoint = excluded.pua_codepoint,
                    source = excluded.source,
                    notes = excluded.notes
                """,
                rows,
            )

    def _normalize_row(self, row: Dict[str, str], source: str | None) -> Dict[str, Optional[str]]:
        data: Dict[str, Optional[str]] = {
            "gaiji_id": row.get("gaiji_id") or row.get("GaijiID"),
            "unicode_codepoint": row.get("unicode_codepoint") or row.get("Unicode"),
            "character": row.get("character") or row.get("Character"),
            "reading": row.get("reading") or row.get("Reading"),
            "radical": row.get("radical") or row.get("Radical"),
            "stroke_count": self._parse_int(row.get("stroke_count") or row.get("StrokeCount")),
            "pua_codepoint": row.get("pua_codepoint") or row.get("PUA"),
            "source": source or row.get("source") or row.get("Source"),
            "notes": row.get("notes") or row.get("Notes"),
        }
        if data["gaiji_id"] is None:
            raise ValueError("gaiji_id is required for every mapping entry")
        return data

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None or value == "":
            return None
        return int(value)

    def get_entry(self, gaiji_id: str) -> Optional[GaijiEntry]:
        cursor = self.connection.execute(
            "SELECT * FROM gaiji_map WHERE gaiji_id = ?", (gaiji_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return GaijiEntry(
            gaiji_id=row["gaiji_id"],
            unicode_codepoint=row["unicode_codepoint"],
            character=row["character"],
            reading=row["reading"],
            radical=row["radical"],
            stroke_count=row["stroke_count"],
            pua_codepoint=row["pua_codepoint"],
            source=row["source"],
            notes=row["notes"],
        )

    def iter_entries(self) -> Iterable[GaijiEntry]:
        cursor = self.connection.execute("SELECT * FROM gaiji_map ORDER BY gaiji_id")
        for row in cursor:
            yield GaijiEntry(
                gaiji_id=row["gaiji_id"],
                unicode_codepoint=row["unicode_codepoint"],
                character=row["character"],
                reading=row["reading"],
                radical=row["radical"],
                stroke_count=row["stroke_count"],
                pua_codepoint=row["pua_codepoint"],
                source=row["source"],
                notes=row["notes"],
            )

    def to_dict(self) -> Dict[str, GaijiEntry]:
        return {entry.gaiji_id: entry for entry in self.iter_entries()}
