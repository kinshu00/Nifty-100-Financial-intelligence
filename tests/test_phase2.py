import sqlite3
from pathlib import Path
import pandas as pd
from src.analytics.ratios import calculate_ratios, cashflow_intelligence, pattern_alerts

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "nifty100.db"


def load():
    conn = sqlite3.connect(DB)
    pnl = pd.read_sql_query("SELECT * FROM profit_loss", conn)
    bs = pd.read_sql_query("SELECT * FROM balance_sheet", conn)
    cf = pd.read_sql_query("SELECT * FROM cash_flow", conn)
    conn.close()
    return pnl, bs, cf


def test_ratio_output_has_expected_rows_and_columns():
    pnl, bs, _ = load()
    result = calculate_ratios(pnl, bs)
    assert len(result) == len(pnl)
    assert {"npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct"}.issubset(result.columns)


def test_ratio_values_are_finite_for_demo_data():
    pnl, bs, _ = load()
    result = calculate_ratios(pnl, bs)
    cols = ["npm_pct", "opm_pct", "roe_pct", "roce_pct", "roa_pct"]
    assert result[cols].notna().all().all()


def test_cashflow_quality_labels_are_valid():
    pnl, _, cf = load()
    result = cashflow_intelligence(pnl, cf)
    assert set(result["cashflow_quality"].dropna().unique()).issubset(
        {"High", "Moderate", "Accrual Risk"}
    )


def test_pattern_alert_columns_exist():
    pnl, bs, cf = load()
    result = pattern_alerts(pnl, bs, cf)
    assert {"distress_alert", "deleveraging"}.issubset(result.columns)
