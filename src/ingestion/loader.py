from pathlib import Path
import pandas as pd

def load_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)

def load_raw_data(raw_dir):
    raw_dir = Path(raw_dir)
    return {
        "companies": load_csv(raw_dir / "companies.csv"),
        "profit_loss": load_csv(raw_dir / "profit_loss.csv"),
        "balance_sheet": load_csv(raw_dir / "balance_sheet.csv"),
        "cash_flow": load_csv(raw_dir / "cash_flow.csv"),
        "stock_prices": load_csv(raw_dir / "stock_prices.csv"),
    }
