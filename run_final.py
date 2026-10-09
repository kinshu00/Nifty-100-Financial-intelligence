from pathlib import Path
import subprocess, sys, json

ROOT=Path(__file__).resolve().parent

def run(script):
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable,script],cwd=ROOT,check=True)

def main():
    for script in ["main.py","run_phase2.py","run_phase3.py","run_phase4.py","run_phase5.py"]:
        run(script)
    from src.decision.engine import build_final_outputs
    summary=build_final_outputs()
    print("\n=== Final Decision Intelligence completed ===")
    for k,v in summary.items(): print(f"{k}: {v}")
    print("\nStart dashboard: streamlit run dashboard.py")
    print("Start API: uvicorn api:app --reload")
if __name__=="__main__":
    main()
