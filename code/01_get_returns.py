"""Step 1: download stock prices (yfinance) and daily factors (Ken French).

Raw files are cached in data/raw/. If a file exists it is reused, so a rerun
gives identical numbers. Pass --refresh to re-download (yfinance adjusted
prices can change after dividends/splits, so a refresh may move results).

Every download is recorded in data/raw/pull_log.csv (source, URL, pull time).

Outputs (raw, committed):
  data/raw/stocks/prices.csv            one row = ticker x trading day (adjusted close)
  data/raw/ken_french/ff3_daily.csv     one row = trading day (factors, in DECIMALS)
"""
import io
import sys
import zipfile
from datetime import datetime, timezone

import pandas as pd
import requests
import yfinance as yf

import config as C

FF_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
          "F-F_Research_Data_Factors_daily_CSV.zip")


def log_pull(file, source, url) -> None:
    row = pd.DataFrame([{
        "file": str(file.relative_to(C.ROOT)).replace("\\", "/"),
        "source": source,
        "url_or_call": url,
        "pulled_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    }])
    old = pd.read_csv(C.PULL_LOG) if C.PULL_LOG.exists() else None
    out = row if old is None else pd.concat([old[old["file"] != row.loc[0, "file"]], row])
    out.to_csv(C.PULL_LOG, index=False)


def get_prices(refresh: bool) -> None:
    path = C.RAW_STOCKS / "prices.csv"
    if path.exists() and not refresh:
        print(f"cached: {path.relative_to(C.ROOT)}")
        return
    C.RAW_STOCKS.mkdir(parents=True, exist_ok=True)
    tickers = list(C.FIRMS) + [C.MARKET_PROXY]
    raw = yf.download(tickers, start=C.START, end=C.END, auto_adjust=True,
                      progress=False, threads=False)
    prices = (raw["Close"].stack().rename("adj_close").reset_index()
              .rename(columns={"Date": "date", "Ticker": "ticker"}))
    prices["date"] = pd.to_datetime(prices["date"]).dt.strftime("%Y-%m-%d")
    prices = prices.sort_values(["ticker", "date"]).reset_index(drop=True)

    assert not prices.duplicated(["ticker", "date"]).any(), "duplicate ticker-date"
    missing = set(tickers) - set(prices["ticker"])
    assert not missing, f"no data for {missing}"

    prices.to_csv(path, index=False)
    log_pull(path, "yfinance (auto_adjust=True Close)",
             f"yf.download({tickers}, start={C.START}, end={C.END})")
    print(f"downloaded {path.relative_to(C.ROOT)}: {prices.shape}")


def get_ff(refresh: bool) -> None:
    path = C.RAW_FF / "ff3_daily.csv"
    if path.exists() and not refresh:
        print(f"cached: {path.relative_to(C.ROOT)}")
        return
    C.RAW_FF.mkdir(parents=True, exist_ok=True)
    resp = requests.get(FF_URL, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")

    # The file has a text header, then the daily table, then a copyright line.
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().startswith(",Mkt-RF"))
    body = []
    for l in lines[start + 1:]:
        if not l.strip() or not l.strip()[0].isdigit():
            break
        body.append(l)
    ff = pd.read_csv(io.StringIO("\n".join([lines[start]] + body)))
    ff = ff.rename(columns={ff.columns[0]: "date"})
    ff["date"] = pd.to_datetime(ff["date"].astype(str).str.strip(), format="%Y%m%d")
    ff = ff[ff["date"] >= "2024-01-01"].copy()
    ff["date"] = ff["date"].dt.strftime("%Y-%m-%d")

    # Ken French reports PERCENT. Convert to decimals so units match returns.
    for col in ["Mkt-RF", "SMB", "HML", "RF"]:
        ff[col] = (ff[col].astype(float) / 100).round(6)
    ff = ff.rename(columns={"Mkt-RF": "mkt_rf", "SMB": "smb", "HML": "hml", "RF": "rf"})

    assert ff["date"].is_unique
    assert ff["mkt_rf"].abs().max() < 0.2, "factor units look like percent, not decimals"
    ff.to_csv(path, index=False)
    log_pull(path, "Ken French Data Library (F-F Research Data Factors, daily)", FF_URL)
    print(f"downloaded {path.relative_to(C.ROOT)}: {ff.shape}, last date {ff['date'].max()}")


def main() -> None:
    refresh = "--refresh" in sys.argv
    get_prices(refresh)
    get_ff(refresh)


if __name__ == "__main__":
    main()
