import sqlite3
from pathlib import Path

def test_database_exists_after_etl():
    db = Path("data/processed/nifty100.db")
    assert db.exists()

def test_expected_tables():
    conn = sqlite3.connect("data/processed/nifty100.db")
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    expected = {"companies", "profit_loss", "balance_sheet", "cash_flow", "stock_prices"}
    assert expected.issubset(tables)
    conn.close()

def test_foreign_key_integrity():
    conn = sqlite3.connect("data/processed/nifty100.db")
    conn.execute("PRAGMA foreign_keys = ON")
    result = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert result == []
    conn.close()
