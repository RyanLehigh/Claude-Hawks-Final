"""Download the real Ornn GPU price index through the Ornn Data API.

    python code/00b_get_ornn.py

Needs ORNN_API_KEY in env/.env (git-ignored; see env/.env.example).
Docs: https://data.ornn.com/docs/introduction

What it calls:
  GET https://api.ornnai.com/api/gpu/{gpu}/history-simple
      ?startDate=...&endDate=...&granularity=daily&limit=...
  with header  Authorization: Bearer <key>

Outputs (PRIVATE, git-ignored -- Ornn's terms forbid redistributing the data):
  data/raw/ornn/ornn_api_raw.json   the API response exactly as received
  data/raw/ornn/ornn_h100.csv       one row = calendar day, in the columns the
                                    pipeline expects (config.ORNN_*_COL)
The pull (endpoint, dates, time) is recorded in data/raw/pull_log.csv. No prices
go in the log.

Not part of run_all.py: auditors have no key, so the pipeline falls back to the
fake file. Run this once by hand, then run_all.py picks the real file up.
"""
import json
import os
from datetime import datetime, timezone
from urllib.parse import quote

import pandas as pd
import requests

import config as C

BASE_URL = "https://api.ornnai.com"
API_GPU_NAME = "H100 SXM"     # Ornn's name for the series; saved as C.ORNN_SERIES ("H100")
START = "2024-01-01"          # ask for more than we need; the API returns what exists
LIMIT = 100_000               # default is 100 rows; docs say there is no upper cap


def read_key() -> str:
    key = os.environ.get("ORNN_API_KEY")
    env_file = C.ROOT / "env" / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "ORNN_API_KEY":
                key = value.strip().strip('"').strip("'")
    if not key:
        raise SystemExit("ORNN_API_KEY not found. Put it in env/.env (see env/.env.example).")
    return key


def log_pull(file: str, call: str) -> None:
    row = pd.DataFrame([{
        "file": file,
        "source": "Ornn Data API (private; key required)",
        "url_or_call": call,
        "pulled_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    }])
    old = pd.read_csv(C.PULL_LOG) if C.PULL_LOG.exists() else None
    out = row if old is None else pd.concat([old[old["file"] != file], row])
    out.to_csv(C.PULL_LOG, index=False)


def main() -> None:
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = f"{BASE_URL}/api/gpu/{quote(API_GPU_NAME)}/history-simple"
    params = {"startDate": START, "endDate": end, "granularity": "daily", "limit": LIMIT}

    r = requests.get(url, params=params, timeout=60,
                     headers={"Authorization": f"Bearer {read_key()}"})
    if r.status_code != 200:
        # Print Ornn's error message, never the key.
        raise SystemExit(f"Ornn API returned {r.status_code}: {r.text[:300]}")
    payload = r.json()
    assert payload.get("success"), f"API did not report success: {str(payload)[:300]}"

    C.RAW_ORNN_PRIVATE.mkdir(parents=True, exist_ok=True)
    (C.RAW_ORNN_PRIVATE / "ornn_api_raw.json").write_text(json.dumps(payload, indent=1))

    df = pd.DataFrame(payload["data"])
    assert {"timestamp", "index_value"} <= set(df.columns), f"unexpected fields: {list(df.columns)}"
    # Daily prints are stamped at MIDNIGHT NEW YORK TIME (04:00 or 05:00 UTC, by
    # daylight saving), i.e. the start of the New York day they average over.
    # So the price date is the New York calendar date of the timestamp.
    ts = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York")
    off_midnight = (ts.dt.strftime("%H:%M:%S") != "00:00:00").sum()
    if off_midnight:
        print(f"WARNING: {off_midnight} timestamps are not at midnight New York time; "
              "check the date mapping")

    out = pd.DataFrame({
        C.ORNN_DATE_COL: ts.dt.date,
        C.ORNN_SERIES_COL: C.ORNN_SERIES,
        C.ORNN_PRICE_COL: df["index_value"].astype(float),
    }).sort_values(C.ORNN_DATE_COL).reset_index(drop=True)

    assert out[C.ORNN_DATE_COL].is_unique, "more than one daily print on the same date"
    assert (out[C.ORNN_PRICE_COL] > 0).all(), "non-positive GPU price"
    if len(out) >= LIMIT:
        print(f"WARNING: got exactly LIMIT={LIMIT} rows; the series may be cut off")

    path = C.RAW_ORNN_PRIVATE / "ornn_h100.csv"
    out.to_csv(path, index=False)

    dates = pd.to_datetime(out[C.ORNN_DATE_COL])
    weekend = (dates.dt.dayofweek >= 5).sum()
    gaps = (dates.diff().dt.days > 1).sum()
    print(f"access tier reported by API: {payload.get('access', 'not given')}")
    print(f"wrote {path.relative_to(C.ROOT)}: {len(out)} days, "
          f"{dates.min().date()} to {dates.max().date()}; "
          f"{weekend} weekend days, {gaps} gaps of more than 1 day")

    log_pull("data/raw/ornn/ornn_h100.csv",
             f"GET {BASE_URL}/api/gpu/{API_GPU_NAME}/history-simple "
             f"startDate={START} endDate={end} granularity=daily")


if __name__ == "__main__":
    main()
