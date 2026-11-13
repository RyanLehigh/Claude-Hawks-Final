"""Step 0: write the FAKE Ornn file (data/raw/ornn_FAKE.csv).

Ornn's real GPU prices are private and never committed. This script makes a
stand-in with the same columns so anyone can run the pipeline.

The fake price is a random walk generated with a fixed seed, independent of
every stock. So on fake data the true compute beta is ZERO for every firm:
any "significant" beta is noise. That makes the fake run a useful check.

One row = GPU model x calendar day (including weekends, since rental markets
trade every day).
"""
import numpy as np
import pandas as pd

import config as C

SEED = 377


def main() -> None:
    rng = np.random.default_rng(SEED)
    dates = pd.date_range("2024-10-01", "2026-10-31", freq="D")

    rows = []
    for model, start_price, vol in [("H100", 2.40, 0.012), ("A100", 1.30, 0.010)]:
        log_p = np.log(start_price) + np.cumsum(rng.normal(0.0, vol, len(dates)))
        rows.append(pd.DataFrame({
            C.ORNN_DATE_COL: dates.strftime("%Y-%m-%d"),
            C.ORNN_SERIES_COL: model,
            C.ORNN_PRICE_COL: np.round(np.exp(log_p), 4),
        }))
    fake = pd.concat(rows, ignore_index=True)

    assert not fake.duplicated([C.ORNN_DATE_COL, C.ORNN_SERIES_COL]).any()
    fake.to_csv(C.ORNN_FAKE, index=False)
    print(f"wrote {C.ORNN_FAKE.relative_to(C.ROOT)}: {fake.shape}, "
          f"{fake[C.ORNN_SERIES_COL].nunique()} series, "
          f"{fake[C.ORNN_DATE_COL].min()} to {fake[C.ORNN_DATE_COL].max()}")


if __name__ == "__main__":
    main()
