from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "processed" / "nifty100.db"
REPORTS = ROOT / "reports"

def _read(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)

def company_universe():
    return _read("SELECT ticker, company_name, sector FROM companies ORDER BY ticker")

def latest_snapshot():
    path = REPORTS / "phase4_company_intelligence.csv"
    risk = REPORTS / "phase4_risk_monitor.csv"
    df = pd.read_csv(path)
    r = pd.read_csv(risk)[["ticker","risk_score","risk_band"]]
    return df.merge(r, on="ticker", how="left")

def screener(sector=None, min_score=0, max_risk=100, min_roe=-np.inf, min_growth=-np.inf,
             stance=None, flag=None):
    df = latest_snapshot()
    if sector and sector.lower() != "all":
        df = df[df.sector.str.lower() == sector.lower()]
    if stance and stance.lower() != "all":
        df = df[df.analyst_stance.str.lower() == stance.lower()]
    if flag and flag.lower() != "all":
        df = df[df.investment_flag.str.lower() == flag.lower()]
    df = df[(df.financial_strength_score >= min_score) &
            (df.risk_score <= max_risk) &
            (df.roe_pct >= min_roe) &
            (df.sales_cagr_pct >= min_growth)]
    return df.sort_values(["financial_strength_score","ticker"], ascending=[False,True])

def peers(ticker):
    df = latest_snapshot()
    m = df[df.ticker.str.upper() == ticker.upper()]
    if m.empty:
        return pd.DataFrame()
    sector = m.iloc[0].sector
    cols = ["ticker","company_name","sector","financial_strength_score","risk_score","roe_pct",
            "opm_pct","npm_pct","roce_pct","debt_to_equity","current_ratio",
            "cfo_pat_ratio","sales_cagr_pct","profit_cagr_pct","analyst_stance","investment_flag"]
    out = df[df.sector == sector][[c for c in cols if c in df.columns]].copy()
    out["peer_score_rank"] = out["financial_strength_score"].rank(ascending=False, method="min").astype(int)
    return out.sort_values("peer_score_rank")

def valuation(ticker):
    df = latest_snapshot()
    m = df[df.ticker.str.upper() == ticker.upper()]
    if m.empty: return None
    row = m.iloc[0]
    p = _read("SELECT date, close FROM stock_prices WHERE ticker=? ORDER BY date", (ticker.upper(),))
    if p.empty: return None
    p["date"] = pd.to_datetime(p["date"])
    latest_price = float(p.iloc[-1]["close"])
    prior_30 = float(p.iloc[max(0,len(p)-31)]["close"])
    prior_90 = float(p.iloc[max(0,len(p)-91)]["close"])
    ret30 = (latest_price/prior_30-1)*100 if prior_30 else np.nan
    ret90 = (latest_price/prior_90-1)*100 if prior_90 else np.nan
    growth = float(row.get("profit_cagr_pct", np.nan))
    quality = float(row.get("financial_strength_score", np.nan))
    # A transparent heuristic signal, not a P/E or intrinsic-value estimate.
    signal = "Attractive" if quality >= 75 and ret90 >= 0 else ("Watch" if quality < 50 or ret90 < -10 else "Neutral")
    return {
        "ticker": row.ticker, "company_name": row.company_name, "sector": row.sector,
        "latest_close": round(latest_price,4), "return_30d_pct": round(ret30,2),
        "return_90d_pct": round(ret90,2), "profit_cagr_pct": round(growth,2),
        "financial_strength_score": round(quality,2), "risk_score": round(float(row.risk_score),2),
        "valuation_signal": signal,
        "methodology": "Quality-growth-momentum heuristic; no market-cap/share-count data is available in the demo dataset."
    }

def portfolio(tickers):
    tickers = [str(x).upper().strip() for x in tickers if str(x).strip()]
    tickers = list(dict.fromkeys(tickers))
    if not tickers:
        return {"tickers":[],"portfolio_return_pct":0,"annualized_volatility_pct":0,"sharpe_ratio":0,"max_drawdown_pct":0}
    series=[]
    valid=[]
    for t in tickers:
        p=_read("SELECT date, close FROM stock_prices WHERE ticker=? ORDER BY date",(t,))
        if len(p):
            s=p.assign(date=pd.to_datetime(p.date)).set_index("date")["close"].pct_change().rename(t)
            series.append(s); valid.append(t)
    if not series:
        return {"tickers":[],"error":"No valid tickers found"}
    returns=pd.concat(series,axis=1).dropna(how="all").fillna(0)
    daily=returns.mean(axis=1)
    wealth=(1+daily).cumprod()
    total=(wealth.iloc[-1]-1)*100
    vol=daily.std(ddof=1)*np.sqrt(252)*100 if len(daily)>1 else 0
    sharpe=(daily.mean()/daily.std(ddof=1))*np.sqrt(252) if len(daily)>1 and daily.std(ddof=1)>0 else 0
    drawdown=wealth/wealth.cummax()-1
    return {"tickers":valid,"portfolio_return_pct":round(float(total),2),
            "annualized_volatility_pct":round(float(vol),2),
            "sharpe_ratio":round(float(sharpe),2),"max_drawdown_pct":round(float(drawdown.min()*100),2),
            "observations":int(len(daily))}

def portfolio_stats():
    df=latest_snapshot()
    return df.groupby("sector").agg(companies=("ticker","count"),
        avg_score=("financial_strength_score","mean"),avg_risk=("risk_score","mean"),
        avg_roe=("roe_pct","mean"),avg_growth=("sales_cagr_pct","mean")).reset_index().round(2)

def risk_alerts():
    df=latest_snapshot()
    return df[df.risk_band.isin(["High","Very High"])].sort_values("risk_score",ascending=False)

def documents():
    files=[]
    for folder in ["analyst_reports","tearsheets"]:
        d=REPORTS/folder
        if d.exists():
            for p in sorted(d.glob("*.md")):
                files.append({"type":folder,"name":p.stem,"filename":str(p.relative_to(ROOT))})
    return files

def document(name):
    safe=Path(name).name
    for folder in ["analyst_reports","tearsheets"]:
        p=REPORTS/folder/safe
        if p.exists() and p.suffix==".md":
            return p.read_text(encoding="utf-8")
    return None

def data_quality():
    checks={}
    with sqlite3.connect(DB_PATH) as conn:
        checks["foreign_key_violations"]=len(conn.execute("PRAGMA foreign_key_check").fetchall())
        for t in ["companies","profit_loss","balance_sheet","cash_flow","stock_prices"]:
            checks[f"{t}_rows"]=int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    return checks

def market_overview():
    df=latest_snapshot()
    p=_read("SELECT ticker, date, close FROM stock_prices")
    p["date"]=pd.to_datetime(p["date"])
    latest=p.sort_values("date").groupby("ticker").tail(1)
    merged=df.merge(latest[["ticker","close"]],on="ticker",how="left")
    return {"companies":int(len(df)),"sectors":int(df.sector.nunique()),
            "avg_score":round(float(df.financial_strength_score.mean()),2),
            "positive":int((df.analyst_stance=="Positive").sum()),
            "caution":int((df.analyst_stance=="Caution").sum()),
            "high_risk":int(df.risk_band.isin(["High","Very High"]).sum()),
            "top_company":str(df.sort_values("financial_strength_score",ascending=False).iloc[0].ticker),
            "latest_prices":merged[["ticker","close"]].fillna("").to_dict("records")}

def company_report(ticker):
    df=latest_snapshot()
    m=df[df.ticker.str.upper()==ticker.upper()]
    if m.empty:return None
    row=m.iloc[0]
    return {"profile":row.fillna("").to_dict(),
            "peers":peers(ticker).fillna("").to_dict("records"),
            "valuation":valuation(ticker),
            "prices":_read("SELECT date,open,high,low,close,volume FROM stock_prices WHERE ticker=? ORDER BY date",(ticker.upper(),)).fillna("").to_dict("records"),
            "financials":_read("""SELECT p.year,p.sales,p.operating_profit,p.net_profit,b.total_debt,
                b.shareholders_equity,c.cash_from_operations,c.capex
                FROM profit_loss p LEFT JOIN balance_sheet b ON p.ticker=b.ticker AND p.year=b.year
                LEFT JOIN cash_flow c ON p.ticker=c.ticker AND p.year=c.year
                WHERE p.ticker=? ORDER BY p.year""",(ticker.upper(),)).fillna("").to_dict("records")}

def build_final_outputs():
    REPORTS.mkdir(exist_ok=True)
    df=latest_snapshot()
    final=df.copy()
    final["screen_rank"]=final["financial_strength_score"].rank(ascending=False,method="min").astype(int)
    final.sort_values("screen_rank").to_csv(REPORTS/"final_screener.csv",index=False)
    portfolio_stats().to_csv(REPORTS/"portfolio_sector_stats.csv",index=False)
    risk_alerts().to_csv(REPORTS/"final_risk_alerts.csv",index=False)
    pd.DataFrame([market_overview()]).to_json(REPORTS/"market_overview.json",orient="records",indent=2)
    summary={
        "phase":"Final Decision Intelligence",
        "companies":int(df.ticker.nunique()),"sectors":int(df.sector.nunique()),
        "api_endpoints":16,"dashboard":"dashboard.py",
        "top_company":str(df.sort_values("financial_strength_score",ascending=False).iloc[0].ticker),
        "high_or_very_high_risk":int(df.risk_band.isin(["High","Very High"]).sum()),
        "data_quality":data_quality()
    }
    (REPORTS/"final_summary.json").write_text(pd.Series(summary).to_json(indent=2),encoding="utf-8")
    return summary
