from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'reports'

def build_phase5():
    intelligence = pd.read_csv(REPORTS / 'phase4_company_intelligence.csv')
    risk = pd.read_csv(REPORTS / 'phase4_risk_monitor.csv')
    sectors = pd.read_csv(REPORTS / 'phase4_sector_intelligence.csv')
    merged = intelligence.merge(risk[['ticker','risk_score','risk_band']], on='ticker', how='left')
    summary = {
        'phase': 5,
        'dashboard': 'dashboard.py',
        'api': 'api.py',
        'companies': int(merged.ticker.nunique()),
        'sectors': int(merged.sector.nunique()),
        'api_endpoints': 7,
        'high_or_very_high_risk': int(merged.risk_band.isin(['High','Very High']).sum()),
        'top_company': str(merged.sort_values('financial_strength_score', ascending=False).iloc[0].ticker),
        'top_sector': str(sectors.sort_values('sector_rank').iloc[0].sector),
    }
    (REPORTS / 'phase5_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    merged.sort_values('financial_strength_score', ascending=False).to_csv(REPORTS / 'phase5_dashboard_dataset.csv', index=False)
    return summary

if __name__ == '__main__':
    print('=== Nifty 100 Financial Intelligence | Phase 5 Dashboard & API ===')
    for k,v in build_phase5().items(): print(f'{k}: {v}')
    print('Phase 5 completed successfully.')
