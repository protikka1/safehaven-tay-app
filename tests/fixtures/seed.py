"""Compatibility wrapper for the authoritative database seed module."""
from database.seed import DEFAULT_DB_PATH, seed_database

if __name__ == "__main__":
    print(f"Initialized {seed_database(DEFAULT_DB_PATH)}")
