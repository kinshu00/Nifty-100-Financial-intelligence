from pathlib import Path
import sqlite3
import json
import numpy as np
import pandas as pd

from src.intelligence.advanced import latest_company_metrics, add_sector_relative_metrics, composite_score, cluster_companies

def load_tables(db_path):
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            "companies": pd.read_sql_query("SELECT * FROM companies", conn),
            "pnl": pd.read_sql_query("SELECT * FROM profit_loss", conn),
            "bs": pd.read_sql_query("SELECT * FROM balance_sheet", conn),
            "cf": pd.read_sql_query("SELECT * FROM cash_flow", conn),
            "prices": pd.read_sql_query("SELECT * FROM stock_prices", conn),
        }
    finally:
        conn.close()
    return tables

def _safe_cagr(first, last, periods):
    if pd.isna(first) or pd.isna(last) or first <= 0 or last <= 0 or periods <= 0:
        return np.nan
    return (last / first) ** (1 / periods) - 1

def build_company_trends(tables):
    pnl, bs, cf = tables["pnl"], tables["bs"], tables["cf"]
    rows = []
    for ticker, g in pnl.sort_values("year").groupby("ticker"):
        g = g.drop_duplicates("year").sort_values("year")
        if len(g) < 2:
            continue
        first, last = g.iloc[0], g.iloc[-1]
        periods = int(last["year"] - first["year"])
        margin_first = first["net_profit"] / first["sales"] * 100 if first["sales"] else np.nan
        margin_last = last["net_profit"] / last["sales"] * 100 if last["sales"] else np.nan

        b = bs[bs["ticker"] == ticker].sort_values("year").drop_duplicates("year")
        c = cf[cf["ticker"] == ticker].sort_values("year").drop_duplicates("year")
        debt_first = b.iloc[0]["total_debt"] if len(b) else np.nan
        debt_last = b.iloc[-1]["total_debt"] if len(b) else np.nan
        cfo = c["cash_from_operations"].sum() if len(c) else np.nan
        pat = g["net_profit"].sum()
        cfo_pat = cfo / pat if pd.notna(cfo) and pat not in (0, np.nan) else np.nan

        rows.append({
            "ticker": ticker,
            "start_year": int(first["year"]),
            "latest_year": int(last["year"]),
            "sales_cagr_pct": _safe_cagr(first["sales"], last["sales"], periods) * 100,
            "profit_cagr_pct": _safe_cagr(first["net_profit"], last["net_profit"], periods) * 100,
            "net_margin_change_pct": margin_last - margin_first,
            "debt_change_pct": ((debt_last / debt_first) - 1) * 100 if pd.notna(debt_first) and debt_first != 0 else np.nan,
            "cfo_pat_period_ratio": cfo_pat,
            "years_available": int(len(g)),
        })
    return pd.DataFrame(rows)

def qualitative_signals(row):
    pros, cons = [], []
    # Profitability
    if row.get("roe_pct", np.nan) >= 15: pros.append("ROE is above 15%, indicating strong equity profitability.")
    elif pd.notna(row.get("roe_pct")) and row["roe_pct"] < 8: cons.append("ROE is below 8%, indicating weaker equity returns.")
    if row.get("opm_pct", np.nan) >= 15: pros.append("Operating margin is strong at 15%+.")
    elif pd.notna(row.get("opm_pct")) and row["opm_pct"] < 8: cons.append("Operating margin is below 8%.")
    # Growth / cash
    if row.get("sales_cagr_pct", np.nan) >= 10: pros.append("Sales CAGR is at least 10%.")
    elif pd.notna(row.get("sales_cagr_pct")) and row["sales_cagr_pct"] < 0: cons.append("Sales have declined over the available history.")
    if row.get("profit_cagr_pct", np.nan) >= 10: pros.append("Profit CAGR is at least 10%.")
    elif pd.notna(row.get("profit_cagr_pct")) and row["profit_cagr_pct"] < 0: cons.append("Net profit has declined over the available history.")
    if row.get("cfo_pat_ratio", np.nan) >= 1: pros.append("Cash generation is strong relative to reported profit.")
    elif pd.notna(row.get("cfo_pat_ratio")) and row["cfo_pat_ratio"] < 0.5: cons.append("Cash conversion is weak relative to reported profit.")
    # Balance sheet
    if pd.notna(row.get("debt_to_equity")) and row["debt_to_equity"] < 0.5: pros.append("Debt-to-equity is below 0.5x.")
    elif pd.notna(row.get("debt_to_equity")) and row["debt_to_equity"] > 1.5: cons.append("Debt-to-equity is above 1.5x.")
    if pd.notna(row.get("current_ratio")) and row["current_ratio"] >= 1.5: pros.append("Current ratio indicates a comfortable short-term liquidity buffer.")
    elif pd.notna(row.get("current_ratio")) and row["current_ratio"] < 1: cons.append("Current ratio is below 1.0x.")
    # Alerts
    if bool(row.get("distress_alert", False)): cons.append("Latest-period distress pattern: negative CFO with positive financing cash flow.")
    if bool(row.get("deleveraging", False)): pros.append("Latest-period data shows a deleveraging signal.")
    return pros, cons

def build_qualitative_intelligence(company_df, trends):
    df = company_df.merge(trends, on="ticker", how="left")
    pros_list, cons_list, confidence = [], [], []
    for _, row in df.iterrows():
        pros, cons = qualitative_signals(row)
        available = sum(pd.notna(row.get(c)) for c in [
            "npm_pct","opm_pct","roe_pct","roce_pct","roa_pct",
            "debt_to_equity","current_ratio","cfo_pat_ratio",
            "sales_cagr_pct","profit_cagr_pct"
        ])
        conf = round(min(100, available / 10 * 100))
        if not pros: pros = ["No strong positive signal triggered by the current rule set."]
        if not cons: cons = ["No major negative signal triggered by the current rule set."]
        pros_list.append(" | ".join(pros))
        cons_list.append(" | ".join(cons))
        confidence.append(conf)
    df["pros"] = pros_list
    df["cons"] = cons_list
    df["insight_confidence_pct"] = confidence
    def stance(r):
        score = r["financial_strength_score"]
        if r["distress_alert"]:
            return "Caution"
        if score >= 75 and r["insight_confidence_pct"] >= 70:
            return "Positive"
        if score < 40:
            return "Caution"
        return "Neutral"
    df["analyst_stance"] = df.apply(stance, axis=1)
    return df

def build_sector_intelligence(df):
    agg = df.groupby("sector").agg(
        companies=("ticker","count"),
        avg_score=("financial_strength_score","mean"),
        median_score=("financial_strength_score","median"),
        avg_roe=("roe_pct","mean"),
        avg_opm=("opm_pct","mean"),
        avg_debt_to_equity=("debt_to_equity","mean"),
        avg_sales_cagr=("sales_cagr_pct","mean"),
        positive_count=("analyst_stance", lambda s: (s=="Positive").sum()),
        caution_count=("analyst_stance", lambda s: (s=="Caution").sum()),
    ).reset_index()
    agg["sector_rank"] = agg["avg_score"].rank(ascending=False, method="min").astype(int)
    return agg.sort_values("sector_rank")

def build_portfolio_risk(df):
    out = df[["ticker","company_name","sector","financial_strength_score","debt_to_equity",
              "current_ratio","cfo_pat_ratio","distress_alert","analyst_stance"]].copy()
    out["risk_score"] = (
        (100 - out["financial_strength_score"]).clip(0,100) * 0.45
        + out["debt_to_equity"].rank(pct=True) * 100 * 0.25
        + (1 - out["current_ratio"].rank(pct=True)) * 100 * 0.15
        + (1 - out["cfo_pat_ratio"].rank(pct=True)) * 100 * 0.15
    ).round(2)
    out["risk_band"] = pd.cut(out["risk_score"], [-np.inf,35,60,75,np.inf],
                              labels=["Low","Moderate","High","Very High"], right=False)
    return out.sort_values("risk_score", ascending=False)

def write_company_reports(df, reports_dir):
    d = Path(reports_dir)/"analyst_reports"
    d.mkdir(parents=True, exist_ok=True)
    for _, r in df.iterrows():
        text = f"""# {r['company_name']} ({r['ticker']})

**Sector:** {r['sector']}  
**Latest year:** {int(r['year'])}  
**Financial Strength Score:** {r['financial_strength_score']:.2f}/100  
**Analyst Stance:** {r['analyst_stance']}  
**Insight Confidence:** {r['insight_confidence_pct']}%

## Key Metrics
- Sales CAGR: {r['sales_cagr_pct']:.2f}% 
- Profit CAGR: {r['profit_cagr_pct']:.2f}%
- ROE: {r['roe_pct']:.2f}%
- ROCE: {r['roce_pct']:.2f}%
- OPM: {r['opm_pct']:.2f}%
- Debt/Equity: {r['debt_to_equity']:.2f}x
- Current Ratio: {r['current_ratio']:.2f}x
- CFO/PAT: {r['cfo_pat_ratio']:.2f}

## Pros
""" + "\n".join(f"- {x.strip()}" for x in str(r["pros"]).split("|")) + "\n\n## Cons\n" + \
"\n".join(f"- {x.strip()}" for x in str(r["cons"]).split("|")) + \
"\n\n> Rule-based analytical output for the project's development/demo dataset. Not investment advice.\n"
        (d/f"{r['ticker']}_analyst_report.md").write_text(text, encoding="utf-8")

def build_phase4(db_path, reports_dir):
    reports = Path(reports_dir); reports.mkdir(parents=True, exist_ok=True)
    tables = load_tables(db_path)
    base = latest_company_metrics(db_path)
    base = add_sector_relative_metrics(base)
    base = composite_score(base)
    base = cluster_companies(base)
    trends = build_company_trends(tables)
    intelligence = build_qualitative_intelligence(base, trends)
    sectors = build_sector_intelligence(intelligence)
    risk = build_portfolio_risk(intelligence)

    intelligence.to_csv(reports/"phase4_company_intelligence.csv", index=False)
    sectors.to_csv(reports/"phase4_sector_intelligence.csv", index=False)
    risk.to_csv(reports/"phase4_risk_monitor.csv", index=False)
    write_company_reports(intelligence, reports)

    summary = {
        "phase": 4,
        "companies": int(intelligence["ticker"].nunique()),
        "sectors": int(intelligence["sector"].nunique()),
        "positive_stance": int((intelligence["analyst_stance"]=="Positive").sum()),
        "neutral_stance": int((intelligence["analyst_stance"]=="Neutral").sum()),
        "caution_stance": int((intelligence["analyst_stance"]=="Caution").sum()),
        "high_risk_or_above": int((risk["risk_band"].isin(["High","Very High"])).sum()),
        "average_insight_confidence_pct": round(float(intelligence["insight_confidence_pct"].mean()),2),
        "top_sector": str(sectors.iloc[0]["sector"]) if len(sectors) else None,
        "top_company": str(intelligence.sort_values("financial_strength_score", ascending=False).iloc[0]["ticker"]),
    }
    (reports/"phase4_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
