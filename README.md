# Claude-Hawks-Final: Which Stocks Are Exposed to GPU Prices?

FIN 331 final project (Seed 15), built with industry partner **Ornn**, a company
that builds markets and price benchmarks for GPU compute.

- **Dashboard:** https://claude-hawks-final-bcfmmhexdwvlz3ekklhhk9.streamlit.app/ (app: [`app.py`](app.py); if it's asleep, click "wake up")
- Dashboard repo: this repo (`app.py` reads only `outputs/`)
- **Presentation:** we present directly from the dashboard above. Its six tabs
  are the talk, in order (question → method → findings → robustness → explore
  a firm → takeaways and limits), written for an audience new to the project.

> **Status: v1 (Checkpoint 4).** Full sample on **real Ornn data**: 28 firms in
> four groups, 569 trading days (2024-06-25 to 2026-09-30), 143 regressions
> (5 specifications × 28 firms, plus 3 group-vs-control tests). GPU timing is now **next-day** (see §4 and §8). Auditors
> without an Ornn key get the fake file automatically. Self-audits:
> [`audits/01_self_audit.md`](audits/01_self_audit.md) (v0),
> [`audits/02_self_audit.md`](audits/02_self_audit.md) (v1).

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
lags); step 5 is a group-minus-control portfolio regression (S6) plus
Benjamini-Hochberg adjusted firm p-values; step 6 has SMB/HML (S2) and a QQQ
Nasdaq control (S4). For step 2, v1 uses **next-day** timing in S1–S4 (the
price dated *d* first counts at the close of *d* + 1) and reports the same-day
version as S5 to show how much timing matters. Both are in
`outputs/robustness_betas.csv`.

## 4b. Results (v1)

All numbers below come from `outputs/compute_betas.csv`,
`outputs/group_summary.csv` and `outputs/group_tests.csv`.

- **No single firm is significantly exposed once we account for testing 28
  firms.** In S1, NOW (p = 0.024) and ADBE (p = 0.038) pass 5% on their own,
  about what chance alone predicts (1.4 of 28). After the Benjamini-Hochberg
  correction, the smallest adjusted p-value is 0.53.
- **Size, where there is a signal:** the largest betas (NOW, SNOW, ADBE, ORCL,
  about 0.06–0.08) mean a stock return of roughly +53 to +73 bp on the day a
  10% rise in the H100 rental price becomes known.
- **Groups vs the control group (S6):** AI-heavy software +0.044 (p = 0.087),
  cloud providers +0.020 (p = 0.42), chipmakers −0.006 (p = 0.85).
  Chipmakers, the group one would expect to gain from higher GPU rents, show
  no exposure at all.
- **Timing matters for individual firms:** several betas move a lot between
  next-day (S1) and same-day (S5) timing, e.g. NOW 0.076 vs −0.002 and META
  0.017 vs −0.040 (`outputs/robustness_betas.csv`).
- **Nasdaq control:** adding the QQQ excess return (S4) barely changes the
  software betas (NOW 0.078, SNOW 0.074, ADBE 0.063), so the weak signal is
  not just a tech-market beta.

**Bottom line so far:** daily H100 rental-price changes explain very little of
daily stock returns over 2024–26. The only hint of exposure is a weak positive
one in AI-heavy software, and it does not survive a multiple-testing correction.

## 5. Dashboard

Built with Streamlit ([`app.py`](app.py)) and doubles as the final
presentation. Six tabs, in talk order:

1. **The question:** what a GPU rental price is, who would care, and the
   one-line answer with headline numbers.
2. **How we measured it:** the compute beta in plain English with a worked
   example, the four steps, and the 28 firms by group (formula and technical
   details in an expander).
3. **What we found:** every firm's compute beta with a 95% range, the
   multiple-testing explanation, and the group-vs-control test (S6).
4. **Does it hold up?** Nasdaq control (S1 vs S4), timing (S1 vs S5), and the
   lead-lag profile averaged by group (S3).
5. **Explore a firm:** pick a firm and specification to see its compute beta,
   range, lead-lag profile, and a ranking filtered by group.
6. **Takeaways and limits:** conclusions, threats to validity, and data notes.

Every number on the page is read or computed from `outputs/` at load time; none
is typed in by hand. The app never reads raw Ornn prices, and shows a warning
banner whenever the results come from fake data.

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
  directly; on 2026-11-20 at 14:52 NY the API had no value stamped 11-20 yet,
  which fits a value appearing only after its day ends. Because the value dated
  *d* also includes hours 0:00–16:00 of *d*, next-day timing is partly stale,
  which biases betas toward zero (it can hide exposure, not create it).
  Weekend moves roll into Monday.
- **Multiple testing:** the "most exposed" of 28 firms can look exposed by
  chance. All firms and specifications are logged. On fake data (true beta = 0),
  1 of 8 firms came out "significant" at 5%. On real data, 2 of 28 do in S1
  (NOW, ADBE), about what chance alone would give (1.4 expected). After a
  Benjamini-Hochberg correction across the 28 firms (`p_bh`), none survives
  (smallest adjusted p = 0.53).
- **Weak control group:** in 2024–26 the defensive controls barely moved with
  the market: KO, JNJ, PG, PEP and DUK have market betas between −0.10 and
  0.07. We checked that this is real, not a data error: the raw yfinance
  prices show no one-day shift (the correlation with SPY is near 0 at lags −1, 0
  and +1), the controls still correlate 0.4–0.6 with each other, and on the
  2025-04-03 tariff shock SPY fell 4.9% while KO, JNJ and DUK rose 2.6–3.0%.
  Defensives traded as their own block in this period. Low-volatility controls
  have mechanically smaller compute betas, so we also report a
  volatility-scaled beta (`std_compute_beta`); the group conclusions are the
  same either way.
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
