import sqlite3
from pathlib import Path
from src.intelligence.advanced import latest_company_metrics, add_sector_relative_metrics, composite_score, cluster_companies, build_screener

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "nifty100.db"

def test_latest_metrics_have_one_row_per_company():
    df = latest_company_metrics(DB)
    assert len(df) == df["ticker"].nunique()
    assert {"npm_pct", "roe_pct", "cfo_pat_ratio", "distress_alert"}.issubset(df.columns)

def test_sector_benchmark_columns_are_added():
    df = add_sector_relative_metrics(latest_company_metrics(DB))
    assert "roe_pct_vs_sector" in df.columns
    assert "debt_to_equity_vs_sector" in df.columns

def test_scores_are_bounded():
    df = composite_score(add_sector_relative_metrics(latest_company_metrics(DB)))
    assert df["financial_strength_score"].between(0, 100).all()
    assert set(df["investment_flag"]).issubset({"Watch", "Neutral", "Strong", "Leader"})

def test_clustering_and_screener():
    df = composite_score(add_sector_relative_metrics(latest_company_metrics(DB)))
    df = cluster_companies(df)
    assert df["cluster"].nunique() >= 1
    screen = build_screener(df)
    assert len(screen) == len(df)
