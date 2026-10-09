# Phase 3 — Advanced Company Intelligence

Phase 3 builds on the Phase 1 ETL/database layer and Phase 2 financial analytics layer.

## Added capabilities
- Latest-company financial intelligence snapshot
- Sector-relative benchmarking
- Composite financial strength score (0–100)
- Automated Leader / Strong / Neutral / Watch flags
- K-Means company clustering (5 clusters where data supports it; `random_state=42`)
- Sector-median imputation + StandardScaler for clustering
- Advanced screener report
- Cluster summary report
- Individual Markdown company tear sheets

## Run

```bash
python -m pip install -r requirements.txt
python run_phase3.py
PYTHONPATH=. pytest -q
```

## New outputs

- `reports/company_intelligence.csv`
- `reports/sector_benchmarks.csv`
- `reports/advanced_screener.csv`
- `reports/cluster_summary.csv`
- `reports/cluster_centers_standardized.csv`
- `reports/phase3_summary.json`
- `reports/tearsheets/*_tearsheet.md`

## Scoring note
The composite score is a screening/analytics heuristic based on percentile ranks across profitability, returns, liquidity, cash conversion and leverage. It is not an investment recommendation.
