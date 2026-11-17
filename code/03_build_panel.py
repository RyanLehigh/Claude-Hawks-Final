"""Step 3: build the analysis panel.

One row = firm x trading day.
Key: (ticker, date), asserted unique.

Columns: ticker, group, date, ret, rf, ret_rf (excess return), mkt_rf, smb,
hml, qqq_rf (QQQ excess return), dgpu, dgpu_nd (alternative timing),
dgpu_lag1.., dgpu_lead1..

Every merge uses validate= and reports how many rows it drops.

Output (git-ignored, contains GPU changes derived from private data):
  data/processed/panel.csv
"""
import pandas as pd

import config as C


def report(label: str, before: int, after: int) -> None:
    print(f"  {label}: {before:,} -> {after:,} rows ({before - after:,} dropped)")


def main() -> None:
    prices = pd.read_csv(C.RAW_STOCKS / "prices.csv", parse_dates=["date"])
    ff = pd.read_csv(C.RAW_FF / "ff3_daily.csv", parse_dates=["date"])
    gpu = pd.read_csv(C.PROCESSED / "gpu_daily.csv", parse_dates=["date"])
    groups = pd.DataFrame({"ticker": list(C.FIRMS), "group": list(C.FIRMS.values())})

    # Nasdaq-100 ETF daily return (one row per date), for the S4 control.
    etf = pd.read_csv(C.RAW_STOCKS / "etf_prices.csv", parse_dates=["date"])
    qqq = etf[etf["ticker"] == C.NASDAQ_PROXY].sort_values("date").copy()
    qqq["ret_qqq"] = qqq["adj_close"].pct_change()
    qqq = qqq.dropna(subset=["ret_qqq"])[["date", "ret_qqq"]]
    assert qqq["date"].is_unique

    # Daily simple returns within each firm (sorted, so pct_change never crosses firms).
    stocks = prices[prices["ticker"].isin(C.FIRMS)].sort_values(["ticker", "date"]).copy()
    stocks["ret"] = stocks.groupby("ticker")["adj_close"].pct_change()
    stocks = stocks.dropna(subset=["ret"]).drop(columns="adj_close")
    assert not stocks.duplicated(["ticker", "date"]).any()

    print("merges:")
    n = len(stocks)
    panel = stocks.merge(groups, on="ticker", how="inner", validate="m:1")
    report("+ group (m:1)", n, len(panel))

    n = len(panel)
    panel = panel.merge(ff, on="date", how="inner", validate="m:1")
    report("+ Ken French factors (m:1)", n, len(panel))

    n = len(panel)
    panel = panel.merge(qqq, on="date", how="inner", validate="m:1")
    report(f"+ {C.NASDAQ_PROXY} return (m:1)", n, len(panel))

    n = len(panel)
    panel = panel.merge(gpu, on="date", how="inner", validate="m:1")
    report("+ GPU change (m:1)", n, len(panel))

    panel["ret_rf"] = panel["ret"] - panel["rf"]
    panel["qqq_rf"] = panel["ret_qqq"] - panel["rf"]
    panel = panel.dropna(subset=["ret_rf", "mkt_rf", "dgpu"])
    panel = panel.sort_values(["ticker", "date"]).reset_index(drop=True)

    assert not panel.duplicated(["ticker", "date"]).any(), "panel key (ticker, date) not unique"
    assert set(panel["ticker"]) == set(C.FIRMS), "a firm fell out of the panel"
    assert panel["ret"].abs().max() < 1, "a daily return above 100%: check the price data"

    cols = (["ticker", "group", "date", "ret", "rf", "ret_rf", "mkt_rf", "smb", "hml", "qqq_rf",
             "dgpu", "dgpu_nd"]
            + [c for c in panel.columns if c.startswith(("dgpu_lag", "dgpu_lead"))])
    panel = panel[cols]
    panel.to_csv(C.PROCESSED / "panel.csv", index=False)
    print(f"wrote data/processed/panel.csv: {panel.shape}, {panel['ticker'].nunique()} firms, "
          f"{panel['date'].min().date()} to {panel['date'].max().date()}")


if __name__ == "__main__":
    main()
