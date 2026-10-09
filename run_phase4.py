from pathlib import Path
from src.intelligence.phase4 import build_phase4

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "processed" / "nifty100.db"
REPORTS = ROOT / "reports"

if __name__ == "__main__":
    print("=== Nifty 100 Financial Intelligence | Phase 4 Qualitative & Risk Intelligence ===")
    summary = build_phase4(DB, REPORTS)
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("\nPhase 4 completed successfully.")
