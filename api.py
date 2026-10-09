import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.app.data_service import load_intelligence, load_sectors, load_risk, company_price_history, company_financial_history

app = FastAPI(title='Nifty 100 Financial Intelligence API', version='1.0.0', description='Phase 5 analyst API over the project demo dataset.')

@app.get('/api/v1/health')
def health():
    df = load_intelligence()
    return {'status':'ok','companies':int(df.ticker.nunique()),'sectors':int(df.sector.nunique())}

@app.get('/api/v1/companies')
def companies(sector: str | None = None, stance: str | None = None, min_score: float = Query(0, ge=0, le=100)):
    df = load_intelligence()
    if sector: df = df[df.sector == sector]
    if stance: df = df[df.analyst_stance == stance]
    df = df[df.financial_strength_score >= min_score]
    return df.fillna('').to_dict(orient='records')

@app.get('/api/v1/companies/{ticker}')
def company(ticker: str):
    df = load_intelligence()
    match = df[df.ticker.str.upper() == ticker.upper()]
    if match.empty: raise HTTPException(status_code=404, detail='Ticker not found')
    row = match.iloc[0].fillna('').to_dict()
    return row

@app.get('/api/v1/companies/{ticker}/prices')
def prices(ticker: str):
    df = company_price_history(ticker.upper())
    if df.empty: raise HTTPException(status_code=404, detail='Price history not found')
    return df.fillna('').to_dict(orient='records')

@app.get('/api/v1/companies/{ticker}/financials')
def financials(ticker: str):
    df = company_financial_history(ticker.upper())
    if df.empty: raise HTTPException(status_code=404, detail='Financial history not found')
    return df.fillna('').to_dict(orient='records')

@app.get('/api/v1/sectors')
def sectors(): return load_sectors().fillna('').to_dict(orient='records')

@app.get('/api/v1/risk')
def risk(): return load_risk().fillna('').to_dict(orient='records')
