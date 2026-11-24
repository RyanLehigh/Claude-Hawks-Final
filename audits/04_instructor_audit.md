# Instructor audit: Claude Hawks, Checkpoint 3

**Repo:** RyanLehigh/Claude-Hawks-Final · **Audited commit:** `b93b430` (2026-11-21 21:45, `main`) · **Seed:** 15, compute costs: which stocks are exposed to GPU prices? (Ornn) · **CP2 audit:** `audits/02_instructor_audit.md` (commit `72122b2`)

> Note from your human teacher: This review is generated with minimal supervision from Opus 5.5-high. It is thorough, but can be too generous at times and doesn't know my taste for what is "good". Grades it and I would assign are correlated, but noisy, ok? If you want additional feedback from _me_, you need to find me before/after/during class or during office hours for a guaranteed speedy reply. I will try to respond to emails and issues, but can not respond to student inquiries around the clock across the final weeks of class. Response times will be unpredictable, though during Thanksgiving week, I will do my best to respond quickly virtually, as in person options will be nil.

## Summary

A real v1: 28 firms in four groups on the real Ornn H100 series, with a pre-registered timing rule, a QQQ control, a group-vs-control test, and Benjamini–Hochberg across firms. All four CP2 findings are fixed.

You also handle the private data well. No Ornn file, price or price change is in the repo or its history, and even the hand checks print "values hidden".

- **Reproduction.** On the committed FAKE series, the pipeline reruns end to end and every hand check passes.
- **Consistency.** Every real-data number I could check from the committed outputs is internally consistent.
- **Independent check.** My own CAPM betas, from your committed prices and factors, match your market betas.

The answer so far is a careful null: no firm survives BH (smallest adjusted p = 0.53). The one thing worth adding before Dec 1 is a weekly version of the test (B1). Because the daily index is an average, daily timing is the weakest link, and 11 of 28 betas change sign between the two timing rules.

## Follow-up on your Checkpoint 2 audit

Response file: `audits/03_audit_response.md` found (on `main`).

| CP2 finding | Status | Evidence |
|---|---|---|
| A1 · `STATUS.md` missing | fixed | `STATUS.md` exists on `main` (`71aafad`, merged in PR #6), with the CP1 memo and current status |
| A2 · No Nasdaq/AI factor control | fixed | `S4_nasdaq` (`ret_rf ~ mkt_rf + qqq_rf + dgpu`) in `outputs/betas_long.csv` for all 28 firms. QQQ is in `data/raw/stocks/etf_prices.csv` and logged in `pull_log.csv` and `specs_tried.md` |
| A3 · GPU timing assumption | fixed | Both mappings are estimated for all 28 firms (`S1_main` next-day, `S5_alt_timing` same-day). The rule is chosen from Ornn's timestamps and docs, before running, and documented (`code/config.py:60-75`, README "Timing"). That it isn't confirmed by Ornn is disclosed |
| A4 · Wrong course number | fixed | `README.md:3` says "FIN 331", and "FIN 377" appears nowhere |

**4 of 4 fixed, 0 still open.**

## Checkpoint 3 checks

| Check | Result |
|---|---|
| Reruns from scratch (full sample) | ⚠️ ✅ `python run_all.py` reruns end to end on the committed FAKE series (exit 0, 30.8 s, 28 firms, all hand checks PASS). The real-data results can't be rerun without the private Ornn file (by design, not counted against you) |
| Inputs have provenance | ✅ `data/raw/pull_log.csv` (Ornn API call, yfinance, French, with pull times) and `data/README.md` |
| Keys unique, merges validated | ✅ `(ticker, date)` asserted, and checked in `hand_checks.txt` |
| No look-ahead / survivorship | ✅ next-day GPU timing (the daily value averages hours after the close). ⚠️ firms chosen today (disclosed) |
| LLM leakage handled | n/a |
| `specs_tried.md` complete | ✅ S1–S6 and BH logged before running (`7781f62` precedes `dfd68e1`) |
| Magnitudes discussed | ✅ `bps_per_10pct_gpu_move` (e.g. NOW: 73 bps on the day a 10% GPU rise becomes known) and volatility-scaled betas |
| Hand checks | ✅ `code/06_hand_checks.py`: one number per step, with private values hidden |
| Threats to validity | ✅ README, including timing, short sample ("one market regime") and hindsight firm choice |
| Every number traces to `outputs/` | ✅ |
| Dashboard matches `outputs/` | ✅ "28" firms, "Days: 569" = `sample_summary.csv` (ORNN, 28 firms, 569 trading days) |

Steps not rerun by design: the real-data run (`code/00b_get_ornn.py` and everything on the Ornn H100 series), because Ornn's data is private and isn't in the repo. The real-data outputs were checked for internal consistency (below). This is not counted against you.

## Getting ready for Dec 1

Presentations run only from URLs, with a hard cutoff at 9 minutes (10:45 section) or 10 minutes (12:10 section). Put your URL(s) in column G of the Team Projects sheet.

| Check | Result |
|---|---|
| Dashboard launches from a clean clone | ✅ `streamlit run app.py --server.headless true --server.port 8613` (venv from `requirements.txt`) on a clean export of `b93b430`: `/_stcore/health` returned `ok` after 3 s. A headless browser clicked all 4 tabs, with no exceptions on the page or in the log |
| Dashboard shows the v1 numbers from `outputs/` | ✅ it reads only `outputs/` (`app.py:23-27`) and shows the ORNN results, labeled "private, not shown" for the price data |
| README links the live URL(s) | ✅ `README.md:6` links the `…streamlit.app` dashboard (the live site itself wasn't checked) |

**Core story for 9–10 minutes:** the question for Ornn; why timing matters with a daily-average index; the compute betas by group with BH (a careful null); then the weekly check (B1) as the robustness that settles whether the null is real or a timing artifact.

## What holds up

- **Private data handled right.** I checked every path ever committed on every branch. Under `data/` there are only `README.md`, `pull_log.csv`, the stock and ETF prices, the French factors and `ornn_FAKE.csv`. `.gitignore` covers `data/raw/ornn/`, `data/processed/` (GPU changes would rebuild the price path) and `env/.env`. No key appears anywhere in the history, and the outputs contain only estimates.
- **The pipeline reruns.** On FAKE data, `run_all.py` builds the 28-firm panel (499 trading days), all 5 specifications, the S6 group tests and the figures, and `06_hand_checks.py` passes every check.
- **Real-data outputs are internally consistent:**
  - in `compute_betas.csv`, t = b/se for all 28 firms (max difference 5e-15);
  - BH recomputed from the `p` column matches `p_bh` (max difference 9e-16);
  - `group_summary.csv` means equal the firm averages;
  - CIs are b ± 1.96·se;
  - `bps_per_10pct_gpu_move` = 953.1 × beta, i.e. ln(1.1)·10⁴, a 10% move in log terms.
- **Independent check of the stock side.** CAPM betas I computed from your committed `prices.csv` and `ff3_daily.csv` over 2024-06-25 to 2026-09-30 match your S1 market betas within 0.011 for all 28 firms (median 0.003). So the return and factor merge on the real run is right.
- **Seed 15 items:**
  - **Changes not levels:** log changes.
  - **Weekend prices:** rolled into Monday.
  - **Many firms ranked:** BH, and every firm logged.
  - **Nasdaq factor:** S4.
  - **Short sample:** disclosed.
  - **Private-data reproducibility:** the FAKE file with the same columns.

## New findings

### B1 · Major · Add a weekly test: the daily index is an average, so daily timing is noisy

**Evidence:** `code/config.py:64-70`: each daily value is "aggregated to a daily average" of hourly prints, stamped at the start of the NY day. Every specification (S1–S6) is daily. In `outputs/betas_long.csv`, 11 of 28 compute betas change sign between next-day (`S1_main`) and same-day (`S5_alt_timing`) timing. In `S3_lead_lag`, at most 2 of 28 firms are significant at 5% in any single lead or lag term, about what chance gives (1.4 expected).

**Why it matters:** An average over a calendar day straddles two trading days' returns whichever way you map it. That pushes daily betas toward zero and scatters them across leads and lags. So the null could be real, or it could be timing. Weekly data mostly removes the problem.

**Fix:** Add `S7_weekly` to `specs_tried.md` before running: Friday-close-to-Friday-close excess returns on market (and QQQ) excess returns and the change in the GPU price over the same week (e.g. Friday's daily value to the next Friday's). Use HAC errors and BH across the 28 firms, as now. Report it next to S1 on the dashboard.

**How to show it's fixed:** `betas_long.csv` has `S7_weekly` rows for all 28 firms, logged before running. I will rerun it on FAKE.

### B2 · Minor · A rerun without the Ornn file overwrites your real results with FAKE ones

**Evidence:** `config.data_source()` returns "FAKE" when `data/raw/ornn/` is empty, and every step writes to the same `outputs/` files. After `python run_all.py` on a fresh clone, `outputs/sample_summary.csv` says `FAKE, 28, 499, …` instead of the committed `ORNN, 28, 569, …`, and every committed result file is replaced.

**Why it matters:** Anyone who reruns your repo (a teammate, me, the final audit) silently replaces the real results in their copy, and could commit them.

**Fix:** When `data_source()` is FAKE, write to `outputs_fake/` (or stop unless `--fake` is given), and say so in the README run steps.

**How to show it's fixed:** On a fresh clone, `python run_all.py` leaves the committed `outputs/` unchanged.

## How to respond

This audit is `audits/04_instructor_audit.md` in your repo. Fix what you can, then add `audits/05_audit_response.md`, replying to each **B** finding (no CP2 findings are still open): fixed (the commit), disputed (why), or disclosed as a limitation (where).

There's no separate deadline for this response. Keep working through these until your final deliverables are due: the final repo is audited again then.
