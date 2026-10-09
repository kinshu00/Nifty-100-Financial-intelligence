from pathlib import Path
import sqlite3
import pandas as pd

TABLES = {
    "companies": "companies",
    "profit_loss": "profit_loss",
    "balance_sheet": "balance_sheet",
    "cash_flow": "cash_flow",
    "stock_prices": "stock_prices",
}

def create_database(db_path, schema_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    schema = Path(schema_path).read_text(encoding="utf-8")
    conn.executescript(schema)
    return conn

def load_to_database(conn, data):
    # Parent table first, then dependent tables.
    for key in ["companies", "profit_loss", "balance_sheet", "cash_flow", "stock_prices"]:
        df = data[key].copy()
        df.to_sql(TABLES[key], conn, if_exists="append", index=False)
    conn.commit()
