from pathlib import Path
from src.analytics.ratios import build_phase2

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "processed" / "nifty100.db"
REPORTS = ROOT / "reports"

if __name__ == "__main__":
    print("=== Nifty 100 Financial Intelligence | Phase 2 Analytics ===")
    summary = build_phase2(DB, REPORTS)
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("\nPhase 2 analytics completed successfully.")
