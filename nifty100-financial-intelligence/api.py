import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

app = FastAPI(title="Nifty 100 Financial Intelligence")


@app.get("/")
def home():
    return {
        "message": "Nifty 100 Financial Intelligence API is running"
    }


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/companies")
def get_companies():
    from src.app.data_service import load_intelligence

    df = load_intelligence()
    return df.fillna("").to_dict(orient="records")

@app.get("/api/v1/companies/{ticker}")
def get_company(ticker: str):
    from app.data_service import load_intelligence
    from fastapi import HTTPException

    df = load_intelligence()

    company = df[
        df["ticker"].astype(str).str.upper() == ticker.upper()
    ]

    if company.empty:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    return company.fillna("").to_dict(orient="records")

@app.get("/api/v1/companies/{ticker}/analysis")
def get_company_analysis(ticker: str):
    from app.data_service import load_intelligence
    from fastapi import HTTPException

    df = load_intelligence()

    company = df[
        df["ticker"].astype(str).str.upper() == ticker.upper()
    ]

    if company.empty:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    row = company.iloc[0]

    return {
        "ticker": row.get("ticker"),
        "company_name": row.get("company_name"),
        "year": row.get("year"),
        "net_profit": row.get("net_profit"),
        "roe_pct": row.get("roe_pct"),
        "roa_pct": row.get("roa_pct"),
        "debt_to_equity": row.get("debt_to_equity"),
        "cashflow_quality": row.get("cashflow_quality"),
        "distress_alert": row.get("distress_alert")
    }

@app.get("/api/v1/screening")
def screen_companies(
    min_roe: float = 15,
    max_debt_to_equity: float = 1.0,
    profitable_only: bool = True
):
    from app.data_service import load_intelligence

    df = load_intelligence()

    if "roe_pct" in df.columns:
        df = df[df["roe_pct"] >= min_roe]

    if "debt_to_equity" in df.columns:
        df = df[df["debt_to_equity"] <= max_debt_to_equity]

    if profitable_only and "net_profit" in df.columns:
        df = df[df["net_profit"] > 0]

    return df.fillna("").to_dict(orient="records")