# Phase 4 — Qualitative, Trend & Risk Intelligence

Phase 4 extends the Phase 3 company-scoring and clustering layer into an analyst-oriented intelligence layer.

## Added capabilities
- Historical sales and profit CAGR
- Net-margin and debt trend analysis
- Cash-conversion trend metric
- Rule-based automated company pros/cons
- Insight confidence score
- Positive / Neutral / Caution analyst stance
- Sector intelligence ranking
- Company-level risk monitor
- Automated analyst Markdown reports for all companies
- Phase 4 JSON summary

## Run

```bash
python -m pip install -r requirements.txt
python run_phase4.py
PYTHONPATH=. pytest -q
```

## New outputs

- `reports/phase4_company_intelligence.csv`
- `reports/phase4_sector_intelligence.csv`
- `reports/phase4_risk_monitor.csv`
- `reports/phase4_summary.json`
- `reports/analyst_reports/*_analyst_report.md`

## Design note

The qualitative layer is deliberately rule-based and reproducible. It does not pretend that generated text is external research or an investment recommendation. All conclusions are derived from the project's financial data and predefined thresholds.
