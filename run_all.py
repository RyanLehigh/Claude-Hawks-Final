"""Rebuild every table and figure from the raw inputs.

    python run_all.py            # use cached raw downloads in data/raw/
    python run_all.py --refresh  # re-download stock prices and factors first

Uses the real Ornn file if one is in data/raw/ornn/ (git-ignored), otherwise
the committed fake file. Stops at the first step that fails.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "00_make_fake_ornn.py",
    "01_get_returns.py",
    "02_load_gpu_prices.py",
    "03_build_panel.py",
    "04_compute_betas.py",
    "05_figures_tables.py",
    "06_hand_checks.py",
]


def main() -> None:
    extra = ["--refresh"] if "--refresh" in sys.argv else []
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        args = [sys.executable, str(ROOT / "code" / step)]
        if step.startswith("01_"):
            args += extra
        subprocess.run(args, cwd=ROOT, check=True)
    print("\nDone. Results are in outputs/.")


if __name__ == "__main__":
    main()
