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

# ---- sample (v1) -----------------------------------------------------------
# Groups are fixed here, before any real-data results were looked at
# (committed on branch v1-results before the first real run).
# v1 = the 28-firm draft list from the README / proposal, unchanged.
FIRMS = {
    # Chipmakers
    "NVDA": "Chipmaker", "AMD": "Chipmaker", "AVGO": "Chipmaker", "TSM": "Chipmaker",
    "INTC": "Chipmaker", "MU": "Chipmaker", "MRVL": "Chipmaker", "ARM": "Chipmaker",
    # Cloud providers (CRWV listed 2025-03-28, so it has a shorter history)
    "AMZN": "Cloud provider", "MSFT": "Cloud provider", "GOOGL": "Cloud provider",
    "ORCL": "Cloud provider", "CRWV": "Cloud provider",
    # AI-heavy software
    "META": "AI-heavy software", "PLTR": "AI-heavy software", "CRM": "AI-heavy software",
    "NOW": "AI-heavy software", "SNOW": "AI-heavy software", "ADBE": "AI-heavy software",
    "AI": "AI-heavy software",
    # Control (no compute exposure)
    "KO": "Control", "PG": "Control", "JNJ": "Control", "WMT": "Control",
    "PEP": "Control", "MCD": "Control", "XOM": "Control", "DUK": "Control",
}
MARKET_PROXY = "SPY"   # downloaded for a hand check; the regressions use Ken French Mkt-RF
# Extra control factor (audit A2): is a compute beta just a Nasdaq/tech beta?
# Kept in its own raw file so adding it does not re-download (and move) prices.csv.
NASDAQ_PROXY = "QQQ"

# The real Ornn H100 series starts 2024-06-23. The sample ends where the Ken
# French daily factors end (2026-09-30 as of the v1 pull).
START = "2024-06-01"   # first stock date requested
END = "2026-11-20"     # last stock date requested (exclusive in yfinance)

# ---- Ornn file layout ------------------------------------------------------
# Column names we expect from Ornn. The fake file uses exactly these.
# TODO(v1): confirm against the real file from the professor.
ORNN_DATE_COL = "date"
ORNN_SERIES_COL = "gpu_model"
ORNN_PRICE_COL = "price_usd_per_gpu_hour"
ORNN_SERIES = "H100"   # the one GPU price series (Ornn API name "H100 SXM")

# ---- GPU price timing (audit A3) -------------------------------------------
# When is the price dated d set, relative to the 4:00 pm ET stock close?
#   "same_day": set before the close on d -> it belongs to trading day d.
#               Main specification (S1-S4), column dgpu.
#   "next_day": set after the close on d -> first known at the close of d + 1
#               calendar day, so it belongs to the next trading day on or after d + 1.
#
# v1 decision: NEXT_DAY is the main timing. Evidence: every daily value from the
# Ornn API is stamped at midnight New York time (04:00/05:00 UTC) = the START of
# the NY day, and Ornn's docs say the index is published hourly and "aggregated
# to a daily average". So the value dated d averages hours after the 4 pm close
# on d, and using it on d would be look-ahead. Same-day stays as the
# alternative (S5). TODO: ask Ornn (data@ornn.com) to confirm the averaging
# window; until they do, GPU_TIMING_CONFIRMED stays False ("inferred from timestamps").
#
# Columns built in step 2: dgpu_sd (same-day rule), dgpu_nd (next-day rule),
# dgpu = the MAIN rule (used by S1-S4 and the leads/lags), dgpu_alt = the other.
GPU_TIMING_MAIN = "next_day"
GPU_TIMING_ALT = "same_day"
GPU_TIMING_CONFIRMED = False

# ---- regressions -----------------------------------------------------------
HAC_LAGS = 5           # Newey-West lags for the standard errors
LEADLAG_K = 2          # leads and lags of the GPU change: t-2 ... t+2
MIN_OBS = 60           # fewer usable days than this -> no estimate (NaN), not a crash


def data_source() -> str:
    """'ORNN' if a real Ornn file is present, otherwise 'FAKE'."""
    return "ORNN" if any(RAW_ORNN_PRIVATE.glob("*.csv")) else "FAKE"
