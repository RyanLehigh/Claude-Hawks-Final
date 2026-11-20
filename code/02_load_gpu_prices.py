"""Step 2: load the GPU price (real Ornn if present, else FAKE) and turn it
into a daily CHANGE on the stock-trading calendar.

Timing rules (see config.py GPU_TIMING_*; v1 main = next_day):
  dgpu    = the main rule's column, dgpu_alt = the other rule's column.
  dgpu_sd ("same_day"): the GPU price dated d is known by the 4:00 pm ET
          stock close on d. The level on trading day t is the last price dated
          on or before t, and dgpu_t = ln level(t) - ln level(previous trading day).
  dgpu_nd ("next_day", audit A3; v1 main): the price dated d is set after
          the close, so it is first known at the close of d + 1 calendar day.
          The level on trading day t is the last price dated on or before t - 1
          calendar day. E.g. Monday's level is Sunday's price, Friday's is
          Thursday's.
  Either way, Saturday/Sunday/holiday moves roll into the next trading day's
  change, and a missing price is filled with the last earlier one.

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

    # Alternative timing: a price dated d becomes usable one calendar day later.
    shifted = gpu.assign(date=gpu["date"] + pd.Timedelta(days=1)).rename(
        columns={"gpu_price": "gpu_price_nd"})
    daily = pd.merge_asof(daily, shifted, on="date", direction="backward")

    daily = daily.dropna(subset=["gpu_price"])

    daily["dgpu_sd"] = np.log(daily["gpu_price"]).diff()
    daily["dgpu_nd"] = np.log(daily["gpu_price_nd"]).diff()
    rule_col = {"same_day": "dgpu_sd", "next_day": "dgpu_nd"}
    daily["dgpu"] = daily[rule_col[C.GPU_TIMING_MAIN]]        # main timing (S1-S4, leads/lags)
    daily["dgpu_alt"] = daily[rule_col[C.GPU_TIMING_ALT]]     # other timing (S5)
    print(f"main GPU timing: {C.GPU_TIMING_MAIN} "
          f"({'confirmed' if C.GPU_TIMING_CONFIRMED else 'inferred, not confirmed by Ornn'})")
    for k in range(1, C.LEADLAG_K + 1):
        daily[f"dgpu_lag{k}"] = daily["dgpu"].shift(k)     # GPU move k trading days BEFORE t
        daily[f"dgpu_lead{k}"] = daily["dgpu"].shift(-k)   # GPU move k trading days AFTER t

    assert daily["date"].is_unique
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    out = daily.drop(columns=["gpu_price", "gpu_price_nd"])   # keep only changes, not levels
    out.to_csv(C.PROCESSED / "gpu_daily.csv", index=False)
    print(f"wrote data/processed/gpu_daily.csv: {out.shape}, "
          f"{out['date'].min().date()} to {out['date'].max().date()}")


if __name__ == "__main__":
    main()
