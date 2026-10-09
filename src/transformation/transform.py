import pandas as pd

def normalize_ticker(df):
    df = df.copy()
    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    return df

def normalize_year(df):
    df = df.copy()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df

def normalize_prices(df):
    df = normalize_ticker(df)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def transform_all(data):
    out = {}

    out["companies"] = normalize_ticker(data["companies"])

    pnl = normalize_year(normalize_ticker(data["profit_loss"]))
    # company_name and sector are master-data attributes and live only in companies.
    out["profit_loss"] = pnl[
        ["ticker", "year", "sales", "operating_profit", "ebitda", "net_profit"]
    ].copy()

    out["balance_sheet"] = normalize_year(normalize_ticker(data["balance_sheet"]))[
        ["ticker", "year", "total_assets", "shareholders_equity", "total_debt",
         "other_liabilities", "current_assets", "current_liabilities"]
    ].copy()

    out["cash_flow"] = normalize_year(normalize_ticker(data["cash_flow"]))[
        ["ticker", "year", "cash_from_operations", "cash_from_investing",
         "cash_from_financing", "capex"]
    ].copy()

    out["stock_prices"] = normalize_prices(data["stock_prices"])
    return out
