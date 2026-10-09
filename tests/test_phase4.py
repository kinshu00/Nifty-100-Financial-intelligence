from pathlib import Path
from src.intelligence.phase4 import (
    load_tables, build_company_trends, latest_company_metrics,
    add_sector_relative_metrics, composite_score, cluster_companies,
    build_qualitative_intelligence, build_sector_intelligence, build_portfolio_risk
)

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "nifty100.db"

def test_company_trends():
    trends = build_company_trends(load_tables(DB))
    assert len(trends) > 0
    assert {"ticker", "sales_cagr_pct", "profit_cagr_pct"}.issubset(trends.columns)

def test_qualitative_intelligence():
    base = cluster_companies(composite_score(add_sector_relative_metrics(latest_company_metrics(DB))))
    out = build_qualitative_intelligence(base, build_company_trends(load_tables(DB)))
    assert len(out) == base["ticker"].nunique()
    assert {"pros","cons","insight_confidence_pct","analyst_stance"}.issubset(out.columns)
    assert out["insight_confidence_pct"].between(0,100).all()
    assert set(out["analyst_stance"]).issubset({"Positive","Neutral","Caution"})

def test_sector_and_risk_reports():
    base = cluster_companies(composite_score(add_sector_relative_metrics(latest_company_metrics(DB))))
    out = build_qualitative_intelligence(base, build_company_trends(load_tables(DB)))
    sectors = build_sector_intelligence(out)
    risk = build_portfolio_risk(out)
    assert len(sectors) > 0
    assert len(risk) == len(out)
    assert set(risk["risk_band"].astype(str)).issubset({"Low","Moderate","High","Very High"})
