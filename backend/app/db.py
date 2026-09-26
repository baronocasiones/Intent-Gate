"""SQLite (WAL) engine — single-file persistence, JSON artifacts on disk."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    artifact_path TEXT
);
"""

def get_db(path: str = "./attestation.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    return conn
