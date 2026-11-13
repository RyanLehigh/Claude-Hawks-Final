# Claude-Hawks-Final: Which Stocks Are Exposed to GPU Prices?

FIN 377 final project (Seed 15), built with industry partner **Ornn**, a company
that builds markets and price benchmarks for GPU compute.

- **Dashboard:** https://claude-hawks-final-bcfmmhexdwvlz3ekklhhk9.streamlit.app/ (app: [`app.py`](app.py); if it's asleep, click "wake up")
- Dashboard repo: this repo (`app.py` reads only `outputs/`)
- Presentation: *TBD (file in this repo)*

> **Status: v0 (Checkpoint 2).** The whole pipeline runs end to end on a small
> sample (8 firms, 2 per group, Nov 2024 – Sep 2026) using a **fake** GPU price
> file, because the real Ornn data hasn't arrived yet. Results on fake data are
> noise by design. Self-audit: [`audits/01_self_audit.md`](audits/01_self_audit.md).

## How to run

```bash
pip install -r requirements.txt
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
| GPU rental prices | Ornn (through the professor) | Daily, ~2 years | **No** |
| Stock prices / returns | yfinance | Daily | Yes |
| Market and factor returns | Ken French Data Library | Daily | Yes |

Each raw file's provenance (source, pull date, and the code that re-downloads
it) is recorded in [`data/README.md`](data/README.md).

### Ornn data rule

Ornn's data is **never posted publicly**: not in this repo, not in the
dashboard, not anywhere else.

- Real Ornn files live in `data/raw/ornn/`, which is git-ignored. Get them from
  the professor.
- So the pipeline runs for anyone, the repo includes a small **fake** file with
  the same columns (`data/raw/ornn_FAKE.csv`). The pipeline uses the real file
  when present and falls back to the fake one otherwise.
- `data/processed/` is git-ignored too: it holds daily GPU price *changes*,
  which would rebuild Ornn's price path. Only regression results go in `outputs/`.

### Open questions about the Ornn data

- Which GPU models, regions, and rental terms are included?
- At what time of day is each day's price set, relative to the 4:00 pm ET stock
  close?
- Are there weekend and holiday prices?

## 3. Dataset

| Dataset | One row is | Key (asserted unique) | Main columns |
|---------|-----------|-----------------------|--------------|
| Analysis panel | firm × trading day | `ticker`, `date` | stock return, market return, factor returns, change in GPU price |
| Results | firm (× specification) | `ticker`, `spec` | compute beta, standard error, lead/lag coefficients, group |

### Sample

**v0 (now):** 8 firms, 2 per group (NVDA, AMD · MSFT, AMZN · META, PLTR · KO, PG),
2024-11-04 to 2026-09-30 (477 trading days). The end date is set by the Ken
French daily factors, which currently stop at 2026-09-30.

**MVP (v1):** about 30 firms in four groups, over the ~2 years the Ornn data
covers. Draft list, to be finalized:

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
with the total count reported. In v0, steps 1–4 are done (with k = 2 leads and
lags); step 5 is a simple group average; step 6 has SMB/HML only.

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
  01_get_returns.py     # yfinance + Ken French downloads (cached, logged)
  02_load_gpu_prices.py # Ornn data (real or FAKE) -> daily change on trading days
  03_build_panel.py     # merge into firm × day panel (validate=, asserts)
  04_compute_betas.py   # same-day, FF3, and lead-lag regressions (HAC)
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
- **Timing:** GPU prices may be set at a different time than the stock close,
  and may exist on weekends. v0 *assumes* a price dated *d* is known by the
  4 pm ET close on *d*. If Ornn sets it later, the same-day beta has
  look-ahead. Weekend moves are rolled into Monday.
- **Multiple testing:** the "most exposed" of 30 firms can look exposed by
  chance. All firms and specifications are logged. On fake data (true beta = 0),
  1 of 8 firms already comes out "significant" at 5%.
- **Weak control group:** KO and PG had market betas near 0 in 2025–26
  (confirmed from raw prices). Low-volatility controls have mechanically
  smaller compute betas, so group comparisons need standardized betas.
- **Stale prices:** missing GPU days are forward-filled, which biases betas
  toward zero. Counted, and to be dropped in v1 if the real data has any.
- **Omitted factors:** the compute beta could be picking up AI sentiment or the
  Nasdaq.
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
