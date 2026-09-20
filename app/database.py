"""SQLite persistence boundary for lead records.

All application SQL belongs in this module. Callers receive plain Python
values rather than SQLite connections, cursors or row objects.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from flask import Flask, current_app, g


DatabaseTarget = Union[str, Path]

_CREATE_LEADS_TABLE = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isim TEXT NOT NULL,
    telefon TEXT NOT NULL,
    mesaj TEXT,
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_INSERT_LEAD = """
INSERT INTO leads (isim, telefon, mesaj)
VALUES (?, ?, ?)
"""

_SELECT_ALL_LEADS = """
SELECT id, isim, telefon, mesaj, tarih
FROM leads
ORDER BY tarih DESC, id DESC
"""


def _resolve_database_target(raw_target: Any) -> DatabaseTarget:
    """Resolve the configured SQLite target and prepare its parent directory."""

    if not isinstance(raw_target, (str, Path)):
        raise RuntimeError("DATABASE_URL geçerli bir SQLite dosya yolu olmalıdır.")

    target = str(raw_target).strip()
    if not target:
        raise RuntimeError("DATABASE_URL boş olamaz.")
    if target == ":memory:":
        return target

    database_path = Path(target).expanduser()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return database_path


def get_db() -> sqlite3.Connection:
    """Return one SQLite connection for the active Flask app context."""

    if "database" not in g:
        target = _resolve_database_target(current_app.config["DATABASE_URL"])
        connection = sqlite3.connect(target)
        connection.row_factory = sqlite3.Row
        g.database = connection

    return g.database


def close_db(_error: Optional[BaseException] = None) -> None:
    """Close and remove the context-local connection, when present."""

    connection = g.pop("database", None)
    if connection is not None:
        connection.close()


def init_db(app: Flask) -> None:
    """Register connection cleanup and create the lead table idempotently."""

    extension_key = "yosuun_database_teardown_registered"
    if not app.extensions.get(extension_key):
        app.teardown_appcontext(close_db)
        app.extensions[extension_key] = True

    with app.app_context():
        connection = get_db()
        connection.execute(_CREATE_LEADS_TABLE)
        connection.commit()


def lead_ekle(isim: str, telefon: str, mesaj: Optional[str] = None) -> int:
    """Insert a lead using bound parameters and return its generated ID."""

    connection = get_db()
    try:
        cursor = connection.execute(_INSERT_LEAD, (isim, telefon, mesaj))
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise

    lead_id = cursor.lastrowid
    cursor.close()
    if lead_id is None:
        raise RuntimeError("SQLite yeni lead için kimlik üretmedi.")
    return int(lead_id)


def tum_leadler() -> List[Dict[str, Any]]:
    """Return every lead newest-first as JSON-serializable dictionaries."""

    cursor = get_db().execute(_SELECT_ALL_LEADS)
    try:
        rows = cursor.fetchall()
    finally:
        cursor.close()
    return [dict(row) for row in rows]
