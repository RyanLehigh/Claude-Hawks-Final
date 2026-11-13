"""Shared settings for every pipeline step.

All paths are relative to the repo root. Run scripts from the repo root
(``python run_all.py`` does this for you).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---- folders ---------------------------------------------------------------
RAW = ROOT / "data" / "raw"
RAW_STOCKS = RAW / "stocks"
RAW_FF = RAW / "ken_french"
RAW_ORNN_PRIVATE = RAW / "ornn"            # git-ignored: real Ornn files go here
ORNN_FAKE = RAW / "ornn_FAKE.csv"          # committed: fake file, same columns
PULL_LOG = RAW / "pull_log.csv"            # provenance: what was downloaded, when
PROCESSED = ROOT / "data" / "processed"    # git-ignored: rebuilt by run_all.py
OUTPUTS = ROOT / "outputs"

# ---- sample (v0) -----------------------------------------------------------
# Groups are fixed here, before any results are looked at.
# v0 uses 2 firms per group; v1 expands to the ~30 firms in the README.
FIRMS = {
    "NVDA": "Chipmaker",
    "AMD": "Chipmaker",
    "MSFT": "Cloud provider",
    "AMZN": "Cloud provider",
    "META": "AI-heavy software",
    "PLTR": "AI-heavy software",
    "KO": "Control",
    "PG": "Control",
}
MARKET_PROXY = "SPY"   # downloaded for a hand check; the regressions use Ken French Mkt-RF

START = "2024-11-01"   # first stock date requested
END = "2026-10-31"     # last stock date requested (exclusive in yfinance)

# ---- Ornn file layout ------------------------------------------------------
# Column names we expect from Ornn. The fake file uses exactly these.
# TODO(v1): confirm against the real file from the professor.
ORNN_DATE_COL = "date"
ORNN_SERIES_COL = "gpu_model"
ORNN_PRICE_COL = "price_usd_per_gpu_hour"
ORNN_SERIES = "H100"   # the one GPU price series used in v0

# ---- regressions -----------------------------------------------------------
HAC_LAGS = 5           # Newey-West lags for the standard errors
LEADLAG_K = 2          # leads and lags of the GPU change: t-2 ... t+2
MIN_OBS = 60           # fewer usable days than this -> no estimate (NaN), not a crash


def data_source() -> str:
    """'ORNN' if a real Ornn file is present, otherwise 'FAKE'."""
    return "ORNN" if any(RAW_ORNN_PRIVATE.glob("*.csv")) else "FAKE"
