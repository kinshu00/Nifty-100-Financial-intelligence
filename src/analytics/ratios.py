from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd


def load_financial_data(db_path):
    conn = sqlite3.connect(db_path)
    pnl = pd.read_sql_query("SELECT * FROM profit_loss", conn)
    bs = pd.read_sql_query("SELECT * FROM balance_sheet", conn)
    cf = pd.read_sql_query("SELECT * FROM cash_flow", conn)
    companies = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return companies, pnl, bs, cf


def safe_divide(num, den):
    den = den.replace(0, np.nan)
    return num / den


def calculate_ratios(pnl, bs):
    df = pnl.merge(
        bs,
        on=["ticker", "year"],
        how="inner",
        suffixes=("_pnl", "_bs"),
    )
    df["npm_pct"] = safe_divide(df["net_profit"], df["sales"]) * 100
    df["opm_pct"] = safe_divide(df["operating_profit"], df["sales"]) * 100
    df["roe_pct"] = safe_divide(df["net_profit"], df["shareholders_equity"]) * 100
    df["roa_pct"] = safe_divide(df["net_profit"], df["total_assets"]) * 100
    capital_employed = df["shareholders_equity"] + df["total_debt"]
    df["roce_pct"] = safe_divide(df["operating_profit"], capital_employed) * 100
    df["debt_to_equity"] = safe_divide(df["total_debt"], df["shareholders_equity"])
    df["current_ratio"] = safe_divide(df["current_assets"], df["current_liabilities"])
    return df


def add_opm_cross_check(df, tolerance_pct=1.0):
    df = df.copy()
    df["opm_from_operating_profit_pct"] = safe_divide(df["operating_profit"], df["sales"]) * 100
    df["opm_cross_check_diff_pct"] = (
        df["opm_pct"] - df["opm_from_operating_profit_pct"]
    ).abs()
    df["opm_check_status"] = np.where(
        df["opm_cross_check_diff_pct"] <= tolerance_pct, "PASS", "REVIEW"
    )
    return df


def cashflow_intelligence(pnl, cf):
    df = pnl.merge(cf, on=["ticker", "year"], how="inner")
    df["cfo_pat_ratio"] = safe_divide(df["cash_from_operations"], df["net_profit"])
    df["capex_intensity_pct"] = safe_divide(df["capex"], df["sales"]) * 100
    df["cashflow_quality"] = pd.cut(
        df["cfo_pat_ratio"],
        bins=[-np.inf, 0.5, 1.0, np.inf],
        labels=["Accrual Risk", "Moderate", "High"],
        right=False,
    ).astype("object")
    df["capex_intensity"] = pd.cut(
        df["capex_intensity_pct"],
        bins=[-np.inf, 3, 8, np.inf],
        labels=["Low", "Moderate", "High"],
        right=False,
    ).astype("object")
    return df


def pattern_alerts(pnl, bs, cf):
    df = pnl.merge(bs, on=["ticker", "year"], how="inner").merge(
        cf, on=["ticker", "year"], how="inner"
    ).sort_values(["ticker", "year"])
    df["prior_debt"] = df.groupby("ticker")["total_debt"].shift(1)
    df["distress_alert"] = (
        (df["cash_from_operations"] < 0) & (df["cash_from_financing"] > 0)
    )
    df["deleveraging"] = (
        (df["cash_from_financing"] < 0)
        & (df["total_debt"] < df["prior_debt"])
    )
    return df


def build_phase2(db_path, reports_dir):
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    companies, pnl, bs, cf = load_financial_data(db_path)

    ratios = add_opm_cross_check(calculate_ratios(pnl, bs))
    cash = cashflow_intelligence(pnl, cf)
    alerts = pattern_alerts(pnl, bs, cf)

    ratios.to_csv(reports_dir / "financial_ratios.csv", index=False)
    cash.to_csv(reports_dir / "cashflow_intelligence.csv", index=False)
    alerts.loc[alerts["distress_alert"]].to_csv(reports_dir / "distress_alerts.csv", index=False)
    alerts.loc[alerts["deleveraging"]].to_csv(reports_dir / "deleveraging_alerts.csv", index=False)

    latest = ratios.sort_values("year").groupby("ticker", as_index=False).tail(1)
    latest = latest.merge(companies, on="ticker", how="left")
    latest.to_csv(reports_dir / "latest_company_snapshot.csv", index=False)

    summary = {
        "companies": int(companies["ticker"].nunique()),
        "ratio_rows": int(len(ratios)),
        "cashflow_rows": int(len(cash)),
        "opm_review_rows": int((ratios["opm_check_status"] == "REVIEW").sum()),
        "distress_alerts": int(alerts["distress_alert"].sum()),
        "deleveraging_alerts": int(alerts["deleveraging"].sum()),
        "cashflow_quality_counts": cash["cashflow_quality"].value_counts(dropna=False).to_dict(),
        "capex_intensity_counts": cash["capex_intensity"].value_counts(dropna=False).to_dict(),
    }
    pd.Series(summary).to_json(reports_dir / "phase2_summary.json", indent=2)
    return summary
