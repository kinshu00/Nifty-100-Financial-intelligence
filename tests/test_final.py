from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.decision.engine import (
    latest_snapshot,screener,peers,valuation,portfolio,portfolio_stats,
    risk_alerts,data_quality,documents
)

def test_final_snapshot():
    df=latest_snapshot()
    assert len(df)>0
    assert {"ticker","financial_strength_score","risk_score","risk_band"}.issubset(df.columns)

def test_screener_filters():
    df=latest_snapshot()
    top=float(df.financial_strength_score.max())
    out=screener(min_score=top-1)
    assert len(out)>=1
    assert (out.financial_strength_score>=top-1).all()

def test_peer_and_valuation():
    ticker=latest_snapshot().iloc[0].ticker
    assert len(peers(ticker))>=1
    v=valuation(ticker)
    assert v["ticker"]==ticker

def test_portfolio_metrics():
    tickers=latest_snapshot().ticker.head(3).tolist()
    out=portfolio(tickers)
    assert set(["portfolio_return_pct","annualized_volatility_pct","sharpe_ratio","max_drawdown_pct"]).issubset(out)

def test_health_and_reports():
    q=data_quality()
    assert q["foreign_key_violations"]==0
    assert q["companies_rows"]>0
    assert len(portfolio_stats())>0
    assert isinstance(risk_alerts(),object)
    assert len(documents())>0
