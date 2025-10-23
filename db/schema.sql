-- SQLite schema for gaiji mapping management
CREATE TABLE IF NOT EXISTS gaiji_map (
    gaiji_id TEXT PRIMARY KEY,
    unicode_codepoint TEXT,
    character TEXT,
    reading TEXT,
    radical TEXT,
    stroke_count INTEGER,
    pua_codepoint TEXT,
    source TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER IF NOT EXISTS gaiji_map_updated_at
AFTER UPDATE ON gaiji_map
FOR EACH ROW BEGIN
    UPDATE gaiji_map SET updated_at = CURRENT_TIMESTAMP WHERE gaiji_id = OLD.gaiji_id;
END;
