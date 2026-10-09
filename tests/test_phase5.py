from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.app.data_service import load_intelligence, load_sectors, load_risk, company_price_history, company_financial_history

def test_phase5_sources():
    companies = load_intelligence(); sectors = load_sectors(); risk = load_risk()
    assert len(companies) > 0
    assert len(sectors) > 0
    assert len(risk) == len(companies)
    assert {'ticker','financial_strength_score','analyst_stance'}.issubset(companies.columns)

def test_company_history():
    companies = load_intelligence()
    ticker = companies.iloc[0].ticker
    assert len(company_price_history(ticker)) > 0
    assert len(company_financial_history(ticker)) > 0
