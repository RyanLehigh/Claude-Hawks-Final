# Data provenance

Every raw input, where it came from, when it was pulled, and the code that
gets it again. Pull times for downloaded files are logged automatically in
[`raw/pull_log.csv`](raw/pull_log.csv).

| File | One row is | Source | How to get it again | Committed? |
|------|-----------|--------|---------------------|------------|
| `raw/stocks/prices.csv` | ticker × trading day: adjusted close | yfinance `yf.download(..., auto_adjust=True)`, 2024-11-01 to 2026-10-30, 8 firms + SPY | `python code/01_get_returns.py --refresh` | Yes |
| `raw/ken_french/ff3_daily.csv` | trading day: Mkt-RF, SMB, HML, RF (**decimals**, converted from percent) | [Ken French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), *Fama/French 3 Factors [Daily]*. Ends 2026-09-30 as of the pull. | `python code/01_get_returns.py --refresh` | Yes |
| `raw/ornn/*.csv` | GPU model × day: rental price | **Ornn, through the professor. Private.** | Ask the professor. Put the file(s) in `data/raw/ornn/`. | **Never** (git-ignored) |
| `raw/ornn_FAKE.csv` | GPU model × calendar day: price | Made up: seeded random walk, unrelated to any stock (true compute beta = 0) | `python code/00_make_fake_ornn.py` | Yes |

`processed/` is rebuilt by `run_all.py` and is git-ignored, because it contains
daily GPU price changes derived from the private Ornn data.

## Expected Ornn columns

Set in `code/config.py`: `date`, `gpu_model`, `price_usd_per_gpu_hour`, with v0
using the `H100` series. **Still unknown:** which regions and rental terms the real
series covers, and what time of day each price is set (see `audits/01_self_audit.md`, #1).
