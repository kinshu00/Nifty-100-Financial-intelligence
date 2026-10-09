# Phase 5 — Interactive Dashboard & API

Phase 5 turns the Phase 4 analytical outputs into a portfolio-ready interface and service layer.

## Added capabilities
- Interactive Streamlit analyst dashboard
- Sector, stance and financial-strength filters
- Company screener with strength and risk scores
- Risk-monitor visualization
- Sector intelligence table
- Company-level price and financial history charts
- Company pros/cons and analyst stance view
- FastAPI REST service with health, company, financial-history, price-history, sector and risk endpoints
- Phase 5 dashboard dataset and JSON summary

## Run dashboard

```bash
python -m pip install -r requirements.txt
python run_phase5.py
streamlit run dashboard.py
```

Open the Streamlit URL shown in the terminal (normally `http://localhost:8501`).

## Run API

```bash
uvicorn api:app --reload
```

Open API documentation at `/docs` on the local server (normally `http://127.0.0.1:8000/docs`).

## Test

```bash
PYTHONPATH=. pytest -q
```

## New outputs
- `dashboard.py`
- `api.py`
- `src/app/data_service.py`
- `run_phase5.py`
- `reports/phase5_dashboard_dataset.csv`
- `reports/phase5_summary.json`
- `tests/test_phase5.py`

The dashboard and API read the existing SQLite database and Phase 4 analytical outputs; they do not modify earlier phases.
