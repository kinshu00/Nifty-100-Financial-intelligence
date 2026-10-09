from pathlib import Path
from src.intelligence.advanced import build_phase3

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "processed" / "nifty100.db"
REPORTS = ROOT / "reports"

if __name__ == "__main__":
    print("=== Nifty 100 Financial Intelligence | Phase 3 Advanced Intelligence ===")
    summary = build_phase3(DB, REPORTS)
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("\nPhase 3 completed successfully.")
