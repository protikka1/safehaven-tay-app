"""SafeHaven SQLite connection helpers."""
from pathlib import Path
import sqlite3

DB_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = DB_DIR / "recovery_app.db"

def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
