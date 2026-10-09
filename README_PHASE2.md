# Nifty 100 Financial Intelligence Platform — Phase 2

## Financial Analytics Layer

Phase 2 extends the Phase 1 ETL/database foundation with reproducible financial analytics.

### Included analytics
- Net Profit Margin (NPM)
- Operating Profit Margin (OPM)
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)
- Debt-to-equity and current ratio
- OPM cross-check with tolerance-based review flag
- CFO/PAT cash-flow quality classification
- CapEx intensity classification
- Distress alert: negative CFO + positive financing cash flow
- Deleveraging alert: negative financing cash flow + declining debt
- Latest company-level analytics snapshot

## Run Phase 2

From the project root:

```bash
python run_phase2.py
```

Then run tests:

```bash
pytest -q
```

## Generated reports

The `reports/` folder contains CSV/JSON outputs generated from the SQLite database:

- `financial_ratios.csv`
- `cashflow_intelligence.csv`
- `distress_alerts.csv`
- `deleveraging_alerts.csv`
- `latest_company_snapshot.csv`
- `phase2_summary.json`

## Important data note

The Phase 1 package uses synthetic development/demo data. The Phase 2 calculations are real implementations, but their outputs should not be interpreted as real-world investment recommendations until official market/financial data is substituted and independently validated.
