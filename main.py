from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.ingestion.loader import load_raw_data
from src.transformation.transform import transform_all
from src.validation.validate import validate_data
from src.database.db import create_database, load_to_database

RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "processed" / "nifty100.db"
SCHEMA = ROOT / "sql" / "schema.sql"

def main():
    print("=== Nifty 100 Financial Intelligence | Phase 1 ETL ===")
    raw = load_raw_data(RAW)
    print("Loaded raw datasets:", ", ".join(raw.keys()))

    data = transform_all(raw)
    errors, warnings = validate_data(data)

    for warning in warnings:
        print("WARNING:", warning)

    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit("ETL stopped because validation failed.")

    if DB.exists():
        DB.unlink()

    conn = create_database(DB, SCHEMA)
    load_to_database(conn, data)

    print("\nETL completed successfully.")
    for table in ["companies", "profit_loss", "balance_sheet", "cash_flow", "stock_prices"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:16s} {count:>6} rows")
    conn.close()

if __name__ == "__main__":
    main()
