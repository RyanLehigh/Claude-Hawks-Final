"""Step 2: load the GPU price (real Ornn if present, else FAKE) and turn it
into a daily CHANGE on the stock-trading calendar.

Timing rule (v0 assumption, see README "Threats"):
  The GPU price dated d is treated as known by the 4:00 pm ET stock close on d.
  For trading day t, dgpu_t = ln P(t) - ln P(previous trading day).
  So Saturday/Sunday/holiday moves roll into the next trading day's change.
  If the price on a trading day is missing, the last earlier price is used.

Leads and lags are built here, on the one-row-per-date series, so they can
never shift across firms by mistake.

Output (git-ignored, because it is derived from private data):
  data/processed/gpu_daily.csv   one row = trading day
"""
import numpy as np
import pandas as pd

import config as C


def load_raw_gpu() -> pd.DataFrame:
    if C.data_source() == "ORNN":
        files = sorted(C.RAW_ORNN_PRIVATE.glob("*.csv"))
        gpu = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        print(f"using REAL Ornn data: {[f.name for f in files]}")
    else:
        gpu = pd.read_csv(C.ORNN_FAKE)
        print(f"using FAKE Ornn data: {C.ORNN_FAKE.name} (true compute beta = 0)")

    need = {C.ORNN_DATE_COL, C.ORNN_SERIES_COL, C.ORNN_PRICE_COL}
    assert need <= set(gpu.columns), f"Ornn file is missing columns {need - set(gpu.columns)}"

    gpu = gpu[gpu[C.ORNN_SERIES_COL] == C.ORNN_SERIES].copy()
    assert len(gpu) > 0, f"no rows for GPU series {C.ORNN_SERIES}"
    gpu["date"] = pd.to_datetime(gpu[C.ORNN_DATE_COL])
    gpu = gpu.rename(columns={C.ORNN_PRICE_COL: "gpu_price"})[["date", "gpu_price"]]

    assert not gpu["date"].duplicated().any(), "more than one GPU price per day"
    assert (gpu["gpu_price"] > 0).all(), "non-positive GPU price"
    return gpu.sort_values("date").reset_index(drop=True)


def main() -> None:
    gpu = load_raw_gpu()

    # The stock-trading calendar comes from the downloaded prices.
    prices = pd.read_csv(C.RAW_STOCKS / "prices.csv", parse_dates=["date"])
    trading_days = pd.DataFrame({"date": np.sort(prices["date"].unique())})

    # Last GPU price on or before each trading day.
    daily = pd.merge_asof(trading_days, gpu, on="date", direction="backward")
    stale = (~daily["date"].isin(gpu["date"])).sum()
    if stale:
        print(f"note: {stale} trading days had no GPU price that day; used the last earlier price")
    daily = daily.dropna(subset=["gpu_price"])

    daily["dgpu"] = np.log(daily["gpu_price"]).diff()
    for k in range(1, C.LEADLAG_K + 1):
        daily[f"dgpu_lag{k}"] = daily["dgpu"].shift(k)     # GPU move k trading days BEFORE t
        daily[f"dgpu_lead{k}"] = daily["dgpu"].shift(-k)   # GPU move k trading days AFTER t

    assert daily["date"].is_unique
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    out = daily.drop(columns="gpu_price")   # keep only changes, not price levels
    out.to_csv(C.PROCESSED / "gpu_daily.csv", index=False)
    print(f"wrote data/processed/gpu_daily.csv: {out.shape}, "
          f"{out['date'].min().date()} to {out['date'].max().date()}")


if __name__ == "__main__":
    main()
