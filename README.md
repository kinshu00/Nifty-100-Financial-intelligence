# Nifty 100 Financial Intelligence Platform

## Phase 1 — Data Foundation & ETL

This phase creates the project's reproducible data foundation:

- Raw financial datasets
- Normalization/transformation
- Data-quality validation
- SQLite relational database
- ETL runner
- Automated database tests

## Run

```bash
python -m pip install -r requirements.txt
python main.py
pytest -q
```

## Database

Generated database:

`data/processed/nifty100.db`

Tables:

- companies
- profit_loss
- balance_sheet
- cash_flow
- stock_prices

## Phase 1 Dataset

The included CSVs are **synthetic development/demo data**, not official market data. They are designed to make the complete pipeline runnable without external API credentials.

Generated on 2026-10-02.
