# Claude-Hawks-Final: Which Stocks Are Exposed to GPU Prices?

FIN 377 final project (Seed 15), built with industry partner **Ornn**, a company
that builds markets and price benchmarks for GPU compute.

> **Status:** planning. This README describes the plan; sections marked *TBD*
> get filled in as the project is built.

- Dashboard: *TBD (link)*
- Dashboard repo: *TBD (link)*
- Presentation: *TBD (file in this repo)*

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
it) is recorded in [`data/README.md`](data/README.md) *(TBD)*.

### Ornn data rule

Ornn's data is **never posted publicly**: not in this repo, not in the
dashboard, not anywhere else.

- Real Ornn files live in `data/raw/ornn/`, which is git-ignored. Get them from
  the professor.
- So the pipeline runs for anyone, the repo includes a small **fake** file with
  the same columns (`data/raw/ornn_FAKE.csv`). The pipeline uses the real file
  when present and falls back to the fake one otherwise.

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

### Sample (MVP)

About 30 firms in four groups, over the ~2 years the Ornn data covers.
Draft list, to be finalized:

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

Every specification run is logged in [`specs_tried.md`](specs_tried.md) *(TBD)*,
with the total count reported.

## 5. Dashboard

- Pick a firm → its compute beta with a confidence interval, and its lead-lag
  profile.
- Ranking of the most exposed firms, colored by group.
- Pages: project intro, methodology, results, interactive exploration.
- Built with Streamlit or a static HTML page on GitHub Pages *(TBD)*. Uses
  only derived results, never raw Ornn prices.

## 6. Planned repo structure

```
run_all.py              # rebuilds every table and figure from raw inputs
code/
  01_get_returns.py     # yfinance + Ken French downloads
  02_load_gpu_prices.py # Ornn data (real or FAKE), compute daily changes
  03_build_panel.py     # merge into firm × day panel (validate=, asserts)
  04_compute_betas.py   # same-day and lead-lag regressions
  05_figures_tables.py  # outputs for slides and dashboard
data/
  raw/                  # downloaded inputs; ornn/ is git-ignored
  processed/            # cleaned intermediate files
outputs/                # every number in the slides and dashboard comes from here
audits/                 # self-audits before each checkpoint
reference/              # course rules and project seed
specs_tried.md          # log of every specification run
STATUS.md               # status memo
```

To reproduce: `python run_all.py` *(TBD)*.

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
  and may exist on weekends.
- **Multiple testing:** the "most exposed" of 30 firms can look exposed by
  chance. All firms and specifications are logged.
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
