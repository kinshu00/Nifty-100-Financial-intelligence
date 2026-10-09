from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ImportError:  # pragma: no cover
    KMeans = None
    StandardScaler = None

from src.analytics.ratios import calculate_ratios, cashflow_intelligence, pattern_alerts

FEATURES = [
    "npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct",
    "debt_to_equity", "current_ratio", "cfo_pat_ratio", "capex_intensity_pct"
]


def load_all(db_path):
    conn = sqlite3.connect(db_path)
    tables = {}
    for table in ["companies", "profit_loss", "balance_sheet", "cash_flow"]:
        tables[table] = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return tables


def latest_company_metrics(db_path):
    t = load_all(db_path)
    ratios = calculate_ratios(t["profit_loss"], t["balance_sheet"])
    cash = cashflow_intelligence(t["profit_loss"], t["cash_flow"])
    alerts = pattern_alerts(t["profit_loss"], t["balance_sheet"], t["cash_flow"])
    latest = ratios.sort_values("year").groupby("ticker", as_index=False).tail(1).copy()
    latest = latest.merge(t["companies"], on="ticker", how="left", suffixes=("", "_company"))
    cash_latest = cash.sort_values("year").groupby("ticker", as_index=False).tail(1)
    latest = latest.merge(cash_latest[["ticker", "cfo_pat_ratio", "capex_intensity_pct", "cashflow_quality", "capex_intensity"]], on="ticker", how="left")
    a = alerts.sort_values("year").groupby("ticker", as_index=False).tail(1)
    latest = latest.merge(a[["ticker", "distress_alert", "deleveraging"]], on="ticker", how="left")
    return latest


def sector_benchmarks(latest):
    agg = latest.groupby("sector")[FEATURES].median().reset_index()
    return agg


def add_sector_relative_metrics(latest):
    df = latest.copy()
    med = df.groupby("sector")[FEATURES].transform("median")
    for col in ["npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct", "current_ratio", "cfo_pat_ratio"]:
        df[f"{col}_vs_sector"] = df[col] - med[col]
    # For debt and capex, lower debt is generally better; lower capex intensity is not inherently better,
    # so only debt gets an inverse interpretation below.
    df["debt_to_equity_vs_sector"] = med["debt_to_equity"] - df["debt_to_equity"]
    df["sector_strength_count"] = sum((df[f"{c}_vs_sector"] > 0).astype(int) for c in ["npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct", "current_ratio", "cfo_pat_ratio", "debt_to_equity"] if f"{c}_vs_sector" in df)
    return df


def composite_score(df):
    out = df.copy()
    positive = ["npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct", "current_ratio", "cfo_pat_ratio"]
    negative = ["debt_to_equity"]
    # Percentile ranks make metrics comparable across different units.
    components = []
    for c in positive:
        r = out[c].rank(pct=True, method="average")
        components.append(r)
        out[f"score_{c}"] = r * 100
    r = 1 - out["debt_to_equity"].rank(pct=True, method="average")
    out["score_debt_to_equity"] = r * 100
    components.append(r)
    out["financial_strength_score"] = (sum(components) / len(components) * 100).round(2)
    out["investment_flag"] = pd.cut(
        out["financial_strength_score"],
        bins=[-np.inf, 40, 60, 75, np.inf],
        labels=["Watch", "Neutral", "Strong", "Leader"],
        right=False,
    ).astype(str)
    return out


def cluster_companies(df, n_clusters=5, random_state=42):
    if KMeans is None or StandardScaler is None:
        raise ImportError("scikit-learn is required for clustering. Install requirements.txt.")
    out = df.copy()
    feature_df = out[FEATURES].copy()
    # Impute by sector median first, then global median for any sector with all missing values.
    feature_df = feature_df.groupby(out["sector"]).transform(lambda s: s.fillna(s.median()))
    feature_df = feature_df.fillna(feature_df.median()).fillna(0)
    X = StandardScaler().fit_transform(feature_df)
    k = min(n_clusters, len(out))
    model = KMeans(n_clusters=k, random_state=random_state, n_init=20)
    out["cluster"] = model.fit_predict(X)
    centers = pd.DataFrame(model.cluster_centers_, columns=FEATURES)
    centers.to_csv(Path("reports") / "cluster_centers_standardized.csv", index=False)
    return out


def build_screener(df):
    cols = ["ticker", "company_name", "sector", "year", "financial_strength_score", "investment_flag", "cluster",
            "npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct", "debt_to_equity", "current_ratio",
            "cfo_pat_ratio", "cashflow_quality", "distress_alert", "deleveraging"]
    return df[[c for c in cols if c in df.columns]].sort_values(["financial_strength_score", "ticker"], ascending=[False, True])


def build_tearsheet(row):
    def f(x, digits=2):
        return "N/A" if pd.isna(x) else f"{x:.{digits}f}"
    return f"""# {row['company_name']} ({row['ticker']})\n\n**Sector:** {row['sector']}  \n**Latest year:** {int(row['year'])}\n\n## Financial Snapshot\n\n| Metric | Value |\n|---|---:|\n| Net Profit Margin | {f(row['npm_pct'])}% |\n| Operating Profit Margin | {f(row['opm_pct'])}% |\n| ROE | {f(row['roe_pct'])}% |\n| ROCE | {f(row['roce_pct'])}% |\n| ROA | {f(row['roa_pct'])}% |\n| Debt / Equity | {f(row['debt_to_equity'])} |\n| Current Ratio | {f(row['current_ratio'])} |\n| CFO / PAT | {f(row['cfo_pat_ratio'])} |\n| Financial Strength Score | {f(row['financial_strength_score'])}/100 |\n| Investment Flag | {row['investment_flag']} |\n| Cluster | {int(row['cluster']) if not pd.isna(row['cluster']) else 'N/A'} |\n\n## Cash-Flow Signals\n- Cash-flow quality: **{row['cashflow_quality']}**\n- Distress alert: **{'YES' if row['distress_alert'] else 'NO'}**\n- Deleveraging signal: **{'YES' if row['deleveraging'] else 'NO'}**\n\n> This is an automated analytical snapshot based on the project's development/demo dataset. It is not investment advice.\n"""


def build_phase3(db_path, reports_dir):
    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)
    latest = latest_company_metrics(db_path)
    latest = add_sector_relative_metrics(latest)
    latest = composite_score(latest)
    latest = cluster_companies(latest)

    benchmarks = sector_benchmarks(latest)
    screener = build_screener(latest)
    latest.to_csv(reports / "company_intelligence.csv", index=False)
    benchmarks.to_csv(reports / "sector_benchmarks.csv", index=False)
    screener.to_csv(reports / "advanced_screener.csv", index=False)

    tear_dir = reports / "tearsheets"
    tear_dir.mkdir(exist_ok=True)
    for _, row in latest.iterrows():
        (tear_dir / f"{row['ticker']}_tearsheet.md").write_text(build_tearsheet(row), encoding="utf-8")

    cluster_summary = latest.groupby("cluster").agg(
        companies=("ticker", "count"),
        avg_score=("financial_strength_score", "mean"),
        avg_roe=("roe_pct", "mean"),
        avg_de=("debt_to_equity", "mean"),
    ).reset_index()
    cluster_summary.to_csv(reports / "cluster_summary.csv", index=False)

    summary = {
        "companies": int(latest["ticker"].nunique()),
        "sectors": int(latest["sector"].nunique()),
        "clusters": int(latest["cluster"].nunique()),
        "leader_count": int((latest["investment_flag"] == "Leader").sum()),
        "strong_count": int((latest["investment_flag"] == "Strong").sum()),
        "neutral_count": int((latest["investment_flag"] == "Neutral").sum()),
        "watch_count": int((latest["investment_flag"] == "Watch").sum()),
        "top_company": str(latest.sort_values("financial_strength_score", ascending=False).iloc[0]["ticker"]),
    }
    pd.Series(summary).to_json(reports / "phase3_summary.json", indent=2)
    return summary
