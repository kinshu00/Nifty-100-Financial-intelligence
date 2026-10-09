from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / 'data' / 'processed' / 'nifty100.db'
REPORTS = ROOT / 'reports'


def query(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def load_intelligence():
    path = REPORTS / 'phase4_company_intelligence.csv'
    if not path.exists():
        raise FileNotFoundError('Run Phase 4 first: python run_phase4.py')
    return pd.read_csv(path)


def load_sectors():
    return pd.read_csv(REPORTS / 'phase4_sector_intelligence.csv')


def load_risk():
    return pd.read_csv(REPORTS / 'phase4_risk_monitor.csv')


def company_price_history(ticker):
    return query('SELECT date, open, high, low, close, volume FROM stock_prices WHERE ticker=? ORDER BY date', (ticker,))


def company_financial_history(ticker):
    return query('''SELECT p.year, p.sales, p.operating_profit, p.net_profit,
                           b.total_debt, b.shareholders_equity,
                           c.cash_from_operations, c.capex
                    FROM profit_loss p
                    LEFT JOIN balance_sheet b ON p.ticker=b.ticker AND p.year=b.year
                    LEFT JOIN cash_flow c ON p.ticker=c.ticker AND p.year=c.year
                    WHERE p.ticker=? ORDER BY p.year''', (ticker,))


def health_summary(df):
    return {
        'companies': int(df.ticker.nunique()),
        'sectors': int(df.sector.nunique()),
        'positive': int((df.analyst_stance == 'Positive').sum()),
        'neutral': int((df.analyst_stance == 'Neutral').sum()),
        'caution': int((df.analyst_stance == 'Caution').sum()),
        'high_risk': int(df.risk_band.isin(['High', 'Very High']).sum()) if 'risk_band' in df else 0,
    }
