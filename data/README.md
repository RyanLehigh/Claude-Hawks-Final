# Data provenance

Every raw input, where it came from, when it was pulled, and the code that
gets it again. Pull times for downloaded files are logged automatically in
[`raw/pull_log.csv`](raw/pull_log.csv).

| File | One row is | Source | How to get it again | Committed? |
|------|-----------|--------|---------------------|------------|
| `raw/stocks/prices.csv` | ticker × trading day: adjusted close | yfinance `yf.download(..., auto_adjust=True)`, 2024-06-01 to 2026-11-19, 28 firms + SPY | `python code/01_get_returns.py --refresh` | Yes |
| `raw/stocks/etf_prices.csv` | ETF × trading day: adjusted close (QQQ, the Nasdaq control in spec S4) | yfinance `yf.download(['QQQ'], ..., auto_adjust=True)`, 2024-06-01 to 2026-11-19. A separate file, so adding it did not re-download `prices.csv`. | `python code/01_get_returns.py --refresh` | Yes |
| `raw/ken_french/ff3_daily.csv` | trading day: Mkt-RF, SMB, HML, RF (**decimals**, converted from percent) | [Ken French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), *Fama/French 3 Factors [Daily]*. Ends 2026-09-30 as of the pull. | `python code/01_get_returns.py --refresh` | Yes |
| `raw/ornn/ornn_h100.csv` | calendar day (New York date): Ornn H100 SXM index, USD per GPU-hour | **Ornn Data API, private.** `GET https://api.ornnai.com/api/gpu/H100%20SXM/history-simple?granularity=daily` ([docs](https://data.ornn.com/docs/introduction)). 880 days, 2024-06-23 to 2026-11-19, including weekends, no gaps. | Put `ORNN_API_KEY` in `env/.env` (key from the professor / Ornn), then `python code/00b_get_ornn.py`. | **Never** (git-ignored) |
| `raw/ornn/ornn_api_raw.json` | the API response exactly as received | same call | same script | **Never** (git-ignored) |
| `raw/ornn_FAKE.csv` | GPU model × calendar day: price | Made up: seeded random walk, unrelated to any stock (true compute beta = 0) | `python code/00_make_fake_ornn.py` | Yes |

`processed/` is rebuilt by `run_all.py` and is git-ignored, because it contains
daily GPU price changes derived from the private Ornn data.

## Ornn columns and timing

`code/00b_get_ornn.py` writes the API data in the columns set in
`code/config.py`: `date`, `gpu_model` (= `H100`), `price_usd_per_gpu_hour`.

**Timestamps:** every daily value is stamped at midnight New York time
(04:00 UTC in summer, 05:00 UTC in winter), i.e. the start of the New York day.
Ornn's docs say the index is published hourly and averaged to a daily value, so
the value dated *d* includes hours after the 4 pm stock close. v1 therefore
counts it on the next trading day (`GPU_TIMING_MAIN = "next_day"`). Not yet
confirmed in writing by Ornn.

**Terms:** Ornn's data-use terms forbid redistributing the data or API
responses, so only regression results are committed (`outputs/`).
