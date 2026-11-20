# Claude-Hawks-Final: Which Stocks Are Exposed to GPU Prices?

FIN 377 final project (Seed 15), built with industry partner **Ornn**, a company
that builds markets and price benchmarks for GPU compute.

- **Dashboard:** https://claude-hawks-final-bcfmmhexdwvlz3ekklhhk9.streamlit.app/ (app: [`app.py`](app.py); if it's asleep, click "wake up")
- Dashboard repo: this repo (`app.py` reads only `outputs/`)
- Presentation: *TBD (file in this repo)*

> **Status: v1 (Checkpoint 4).** Full sample on **real Ornn data**: 28 firms in
> four groups, 569 trading days (2024-06-25 to 2026-09-30), 5 specifications =
> 140 regressions. GPU timing is now **next-day** (see §4 and §8). Auditors
> without an Ornn key get the fake file automatically. v0 self-audit:
> [`audits/01_self_audit.md`](audits/01_self_audit.md).

## How to run

```bash
pip install -r requirements.txt
python code/00b_get_ornn.py    # only with an Ornn key in env/.env: downloads the real GPU data
python run_all.py              # rebuilds data/processed/ and outputs/ from data/raw/
python run_all.py --refresh    # same, but re-downloads stock prices and factors first
streamlit run app.py           # dashboard, reads outputs/ only
```

`run_all.py` uses the real Ornn file if one is in `data/raw/ornn/` (git-ignored)
and the committed fake file otherwise. Every output says which one it used
(`data_source` = `ORNN` or `FAKE`). The last step, `code/06_hand_checks.py`,
recomputes one number per step by hand and stops the run if any don't match.

---

## 1. Question

Which companies' share prices are most exposed to the cost of compute?

1. Do GPU rental prices and stock returns move together on the same day?
2. Do changes in compute prices **lead or lag** changes in stocks?
3. Does exposure differ across chipmakers, cloud providers, AI-heavy software,
   and firms with no compute exposure?

**Who would pay for the answer:** Ornn and its customers (anyone hedging
compute costs), a portfolio manager sizing AI exposure, or a CFO whose margins
depend on GPUs.

## 2. Data

| Input | Source | Frequency | Public? |
|-------|--------|-----------|---------|
| GPU rental prices | Ornn Data API, H100 SXM daily index (API key required) | Daily incl. weekends, 2024-06-23 → | **No** |
| Stock prices / returns | yfinance | Daily | Yes |
| Market and factor returns | Ken French Data Library | Daily | Yes |

Each raw file's provenance (source, pull date, and the code that re-downloads
it) is recorded in [`data/README.md`](data/README.md).

### Ornn data rule

Ornn's data is **never posted publicly**: not in this repo, not in the
dashboard, not anywhere else.

- Real Ornn files live in `data/raw/ornn/`, which is git-ignored.
  `code/00b_get_ornn.py` downloads them with an API key kept in the git-ignored
  `env/.env`.
- So the pipeline runs for anyone, the repo includes a small **fake** file with
  the same columns (`data/raw/ornn_FAKE.csv`). The pipeline uses the real file
  when present and falls back to the fake one otherwise.
- `data/processed/` is git-ignored too: it holds daily GPU price *changes*,
  which would rebuild Ornn's price path. Only regression results go in `outputs/`.

### What we learned from the Ornn data (v1)

- **Weekends:** yes, there is a price every calendar day (880 days, no gaps).
  Weekend moves roll into Monday.
- **Time of day:** every daily value is stamped at midnight New York time, and
  Ornn's docs say the index is an hourly series averaged to a daily value. So
  the value dated *d* includes hours after the 4 pm close, and v1 counts it on
  the next trading day. This is our inference from the data and docs.
- **Still open:** which regions and rental terms feed the H100 index (the API
  only reports a "global" region).

## 3. Dataset

| Dataset | One row is | Key (asserted unique) | Main columns |
|---------|-----------|-----------------------|--------------|
| Analysis panel | firm × trading day | `ticker`, `date` | stock return, market return, factor returns, change in GPU price |
| Results | firm (× specification) | `ticker`, `spec` | compute beta, standard error, lead/lag coefficients, group |

### Sample

**v0:** 8 firms, 2 per group, 2024-11-04 to 2026-09-30, fake GPU data.

**v1 (now):** the 28 firms below, 2024-06-25 to 2026-09-30 (569 trading days,
15,741 firm-days). The start is set by the Ornn data (first price 2024-06-23),
the end by the Ken French daily factors, which currently stop at 2026-09-30.
The list is the draft list from the proposal, unchanged, and was committed
before the first real-data run:

| Group | Candidate tickers |
|-------|-------------------|
| Chipmakers | NVDA, AMD, AVGO, TSM, INTC, MU, MRVL, ARM |
| Cloud providers | AMZN, MSFT, GOOGL, ORCL, CRWV\* |
| AI-heavy software | META, PLTR, CRM, NOW, SNOW, ADBE, AI |
| Control (no compute exposure) | KO, PG, JNJ, WMT, PEP, MCD, XOM, DUK |

\* CoreWeave listed in March 2025, so it has a shorter history.

Groups are assigned **before** looking at results, and every firm stays in the
results table whether or not its estimate is interesting.

## 4. Method

1. **Use changes, not levels.** Convert the GPU price to a daily percent change
   (or log change) to avoid two trending series looking related.
2. **Align timing.** Match each GPU price observation to the correct stock
   trading day based on when it is set. Decide how weekend GPU price changes
   are rolled into Monday.
3. **Same-day compute beta.** For each firm:

   `r_it − rf_t = α_i + β_i^MKT (MKT_t − rf_t) + β_i^GPU ΔGPU_t + ε_it`

   `β_i^GPU` is the firm's **compute beta**. Use robust (HAC) standard errors.
4. **Leads and lags.** Add ΔGPU at t−k … t+k (e.g. k = 1 to 5 days) to test
   whether compute prices lead or lag stock returns.
5. **Compare groups.** Average compute betas by group and test whether the
   exposed groups differ from the control group.
6. **Robustness.** Add a Nasdaq/tech factor and other factors (Fama-French) to
   check that the compute beta is not just an AI-sentiment or Nasdaq factor in
   disguise. Check subperiods.

Every specification run is logged in [`specs_tried.md`](specs_tried.md),
with the total count reported. So far, steps 1–4 are done (with k = 2 leads and
lags); step 5 is a simple group average; step 6 has SMB/HML (S2) and a QQQ
Nasdaq control (S4). For step 2, v1 uses **next-day** timing in S1–S4 (the
price dated *d* first counts at the close of *d* + 1) and reports the same-day
version as S5 to show how much timing matters. Both are in
`outputs/robustness_betas.csv`.

## 5. Dashboard

- Pick a firm → its compute beta with a confidence interval, and its lead-lag
  profile.
- Ranking of the most exposed firms, colored by group.
- Pages: project intro, methodology, results, interactive exploration.
- Built with Streamlit ([`app.py`](app.py)), with tabs for Intro, Methodology,
  Results, and Explore. Uses only derived results from `outputs/`, never raw
  Ornn prices. Shows a warning banner whenever the results come from fake data.

## 6. Repo structure

```
run_all.py              # rebuilds every table and figure from raw inputs
app.py                  # Streamlit dashboard (reads outputs/ only)
requirements.txt
code/
  config.py             # paths, firms and groups, dates, regression settings
  00_make_fake_ornn.py  # writes the FAKE Ornn file (seeded; true beta = 0)
  00b_get_ornn.py       # downloads the REAL Ornn data via API (needs a key; run by hand)
  01_get_returns.py     # yfinance + Ken French downloads (cached, logged)
  02_load_gpu_prices.py # Ornn data (real or FAKE) -> daily change on trading days
  03_build_panel.py     # merge into firm × day panel (validate=, asserts)
  04_compute_betas.py   # S1-S5: main, FF3, lead-lag, Nasdaq control, alt. timing (HAC)
  05_figures_tables.py  # tables and figures for the slides and dashboard
  06_hand_checks.py     # one number per step recomputed by hand
data/
  README.md             # provenance of every raw input
  raw/                  # downloaded inputs + pull_log.csv; ornn/ is git-ignored
  processed/            # git-ignored (contains GPU changes); rebuilt by run_all.py
outputs/                # every number in the slides and dashboard comes from here
audits/                 # self-audits before each checkpoint
reference/              # course rules and project seed
specs_tried.md          # log of every specification run
```

## 7. Timeline

| Date | Checkpoint | Deliverable |
|------|------------|-------------|
| Fri Oct 23 | 1. Pick + proof of concept | Real rows for 3–5 firms, `STATUS.md` |
| Mon Nov 9 | 2. v0, end to end | Full pipeline on a small sample, dashboard skeleton, `audits/01_self_audit.md` |
| Thu Nov 12 | 3. Proposal (HW8) | Polished proposal document with dashboard mockup |
| Thu Nov 19 | 4. v1 results | Full sample; AI audit returned |
| Dec 1 / Dec 3 | 5. Present | Final repo audited again |

## 8. Threats to validity

- **Spurious correlation:** trending series look related; we use changes, not levels.
- **Timing:** Ornn stamps each daily value at midnight New York time and
  describes it as an average of hourly prints, so the value dated *d* includes
  after-close hours. v1 counts it on the next trading day (S1–S4) to avoid
  look-ahead; the same-day version (S5) is reported only for comparison. This
  is inferred from timestamps and Ornn's public docs, not confirmed by Ornn
  directly. If the
  averaging window ended before 4 pm, next-day timing would be stale rather
  than look-ahead, which biases betas toward zero. Weekend moves roll into Monday.
- **Multiple testing:** the "most exposed" of 28 firms can look exposed by
  chance. All firms and specifications are logged. On fake data (true beta = 0),
  1 of 8 firms came out "significant" at 5%. On real data, 2 of 28 do in S1
  (NOW, ADBE), about what chance alone would give (1.4 expected); no
  multiple-testing correction has been applied yet.
- **Weak control group:** KO and PG had market betas near 0 in 2025–26
  (confirmed from raw prices). Low-volatility controls have mechanically
  smaller compute betas, so group comparisons need standardized betas.
- **Stale prices:** missing GPU days would be forward-filled, which biases
  betas toward zero. The real H100 series has no missing days (880 of 880), so
  nothing is forward-filled in v1. Whether Ornn's index itself moves slowly
  (smoothing within its hourly average) is not tested.
- **Omitted factors:** the compute beta could be picking up AI sentiment or the
  Nasdaq. S4 controls for the QQQ excess return. QQQ is highly correlated with
  the market, so S4 tests whether the GPU coefficient survives, not what the
  Nasdaq coefficient is. An AI-specific basket is not controlled for yet.
- **Short sample:** about two years is one market regime.
- **Survivorship / look-ahead:** firm list chosen from today's knowledge of
  which companies are "AI stocks."
- **Private data:** auditors run the pipeline on fake Ornn data, so real
  results can't be fully reproduced without access from the professor.

## 9. Stretch goals

- How well GPU futures would hedge compute costs
- How auction and order-book market designs compare
- How GPU model, region, and rental term affect building a benchmark price

## Team

*TBD*
