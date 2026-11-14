# Self-audit 01: Checkpoint 2 (v0)

**Date:** 2026-11-13 · **Branch:** `checkpoint-2` · **Data:** FAKE Ornn file (real file not yet received)

**How this was run:** the *Skeptical review* prompt (Quick Reference, *Starter prompts
for coding agents*, #5) was given verbatim to Claude Code on this repo:

> Review this repo like a skeptical finance professor. Look for look-ahead bias and
> leakage, merges without validate, unit and frequency mismatches, hard-coded paths or
> keys, and steps that don't reproduce from run_all.py. List issues ranked by severity;
> don't fix anything yet.

**Caveat on independence:** the same agent session that helped write the v0 code also
ran this review, so it may be blind to its own mistakes. Before v1, a teammate should
rerun the prompt in a fresh session and add anything new below.

---

## 1. What it flagged, and which findings are real

Ranked by severity, as reported. "Real?" is our judgment after checking.

| # | Severity | Finding | Real? | Evidence |
|---|----------|---------|-------|----------|
| 1 | High | **GPU price timing is assumed, not known.** Step 2 treats a GPU price dated *d* as known by the 4 pm ET close on *d*. If Ornn stamps prices at, say, midnight UTC (8 pm ET), the "same-day" change contains after-close information: a look-ahead that would inflate same-day betas. | **Real, open.** | `code/02_load_gpu_prices.py` docstring. We have no Ornn metadata yet. |
| 2 | High | **Private data can leak through derived files.** `data/processed/` was not git-ignored, and it holds daily GPU *changes*, which rebuild Ornn's price path up to a constant. `outputs/hand_checks.txt` also printed one actual GPU change. With real data, a `git add .` would publish Ornn data. | **Real, fixed.** | `.gitignore` had only `data/raw/ornn/`. Hand-check line "GPU change on Monday ... pipeline=-0.0098". |
| 3 | Medium | **Multiple testing.** 3 specs × 8 firms, plus 5 lead/lag terms per firm. On FAKE data, where every true compute beta is 0 by construction, META still shows p = 0.019. Without a correction, the "most exposed" firm will often be noise. | **Real, open.** | `outputs/compute_betas.csv`, META row. |
| 4 | Medium | **Weak control group.** KO and PG have market betas of −0.04 and 0.10 over 2024-11 to 2026-09. A low-volatility control has mechanically smaller compute betas and SEs, so "AI firms have bigger compute betas than the control group" could just mean "AI stocks are more volatile." | **Real, open.** Not a pipeline bug: KO vs SPY computed straight from raw prices gives the same −0.05, and shifting dates ±1 day doesn't fix it. | `outputs/hand_checks.txt` (INFO line). |
| 5 | Medium | **Firm selection uses hindsight.** Groups (e.g. PLTR as "AI-heavy software") are chosen with 2026 knowledge of which stocks became "AI stocks." | **Real, open.** Disclosed in the README. | `code/config.py` `FIRMS`. |
| 6 | Medium | **Omitted factor.** The only robustness spec adds SMB and HML. Nothing yet controls for a tech/Nasdaq or AI-sentiment factor, so a compute beta could just be AI beta. | **Real, open.** | `code/04_compute_betas.py` `SPECS`. |
| 7 | Low | **Stale GPU prices are forward-filled.** `merge_asof(direction="backward")` fills missing GPU days with the last price. That gives a zero change on the missing day and a catch-up jump later, which biases betas toward zero. | **Real, open** (no missing days in the fake file, so no effect yet). | `code/02_load_gpu_prices.py`. |
| 8 | Low | **Sample silently ends early.** Ken French daily factors currently end 2026-09-30, so the inner merge drops October 2026 (176 firm-days). The log prints the drop, but the README didn't mention it. | **Real, fixed** (documented). | Step 3 log: "3,992 -> 3,816 rows (176 dropped)". |
| 9 | Low | **A hand check could silently skip.** The Monday GPU-change check ran only `if` the prior Friday was a trading day, so it could pass without checking anything. | **Real, fixed.** | Old `code/06_hand_checks.py`. |
| 10 | Low | **`--refresh` changes the numbers.** yfinance adjusted prices are revised after dividends and splits, so a re-download can move results slightly. | **Real, handled.** The default `run_all.py` uses the committed raw files. `data/raw/pull_log.csv` records when each was pulled. | `code/01_get_returns.py`. |
| 11 | Low | **Ornn column names are a guess.** The fake file's columns (`date`, `gpu_model`, `price_usd_per_gpu_hour`) may not match the real file. | **Real, open.** If they differ, step 2 stops with a clear error naming the missing columns. | `code/config.py` TODO. |
| — | Checked, clean | **Merges without `validate=`:** none. All five merges use `validate=` (m:1 or 1:1), and drops are printed. | Not an issue. | `code/03_build_panel.py`, `04`, `06`. |
| — | Checked, clean | **Unit and frequency mismatches:** Ken French is in percent and is converted to decimals, with an assert. SPY excess return vs. Mkt-RF has a correlation of 0.994 (same units, same dates). Everything is daily. | Not an issue. | `outputs/hand_checks.txt`. |
| — | Checked, clean | **Hard-coded paths or keys:** none. Paths are relative to the repo root (`code/config.py`). `env/.env` is git-ignored, and the Ornn API key in it is unused. | Not an issue. | `git grep` for `C:\`, `/Users/`, `API_KEY`. |
| — | Checked, clean | **Reproduces from `run_all.py`:** yes. It ran end to end twice from the cached raw files with identical numbers, and it passed on the real-data code path with a stand-in file. | Not an issue. | See section 2. |

## 2. What we fixed in this PR, and what's still open

### Fixed in this PR
- **#2 Private-data leak:** `data/processed/` is git-ignored. Hand checks that touch Ornn
  data now print "values hidden" when the real file is used. Tested by dropping a
  stand-in file into `data/raw/ornn/`: outputs are tagged `ORNN`, and no GPU number reaches `outputs/`.
- **#8 Sample end date:** documented in the README and on the dashboard's Intro page (sample dates come from `outputs/sample_summary.csv`).
- **#9 Silent hand check:** the check now picks a Monday whose Friday was a trading day, so it always runs.
- **Market-beta guard (found while building):** the hand check that failed on KO's
  near-zero beta was split. Tech and AI firms must have a beta above 0.5 (near zero would mean
  misaligned dates). Control betas are reported, not asserted.

### Still open, with the plan

| # | Issue | Plan | When |
|---|-------|------|------|
| 1 | GPU price timestamp | Ask the professor / Ornn what time each daily price is set. If it's after 4 pm ET, shift the GPU series one trading day back so the "same-day" change is fully known at the close. The S3 lead/lag terms already show whether the k = +1 coefficient is large. | Before v1 (Nov 19) |
| 3 | Multiple testing | Report Holm-adjusted p-values across firms. Use the FAKE-data run as a placebo: report its false-positive rate next to the real results. Keep logging every spec in `specs_tried.md`. | v1 |
| 4 | Weak control | Report **standardized** compute betas (effect of a 1-SD GPU move in units of the stock's own residual SD) so groups with different volatility compare fairly. Consider adding higher-beta non-compute controls (industrials, banks). | v1 |
| 5 | Hindsight in firm choice | Freeze the 30-firm list and its groups in `config.py` in one commit *before* running real data, and say so in the README. | Before v1 |
| 6 | Omitted AI/Nasdaq factor | Add a spec with the QQQ-minus-SPY return (or an AI-basket return) as a control. | v1 |
| 7 | Stale GPU prices | Count stale days in the real data. If there are any, drop them (and the following day) instead of forward-filling, and log it as a spec. | When real data arrives |
| 11 | Real Ornn columns | Map the real column names in `config.py`. Steps 2 and 6 read them from there. | When real data arrives |

## 3. Checklist from `00_PROJECT_SEEDS`

| # | Item | Status | Note |
|---|------|--------|------|
| 1 | It reproduces | **OK** | `python run_all.py` rebuilds every output from the committed raw files. Also run from a fresh clone (see the PR description). |
| 2 | Every input has a provenance | **Problem** | Stocks and factors: OK (`data/raw/pull_log.csv`, `data/README.md`, code that re-downloads). Ornn: we don't yet know the GPU models, regions, rental terms, or timestamp of the real series. |
| 3 | Unit of observation | **OK** | Panel row = firm × trading day, key `(ticker, date)` asserted unique. Results row = firm × spec × term. Every merge uses `validate=`. |
| 4 | No look-ahead | **Problem** | GPU price timing relative to the close is unverified (#1). Firm groups use hindsight (#5). |
| 5 | No LLM leakage | **OK** | Not applicable: no LLM produces any variable in this project. |
| 6 | No p-hacking | **OK** | `specs_tried.md` logs all 3 specs × 8 firms = 24 regressions. A multiple-testing correction is still to come (#3). |
| 7 | Magnitudes, not just stars | **Not yet** | `bps_per_10pct_gpu_move` is in the results table, but it's meaningless on fake data. We'll judge size against a real hedging question once we have Ornn data. |
| 8 | Checks by hand | **OK** | `code/06_hand_checks.py`: one number per step recomputed independently (a return, the factor units, a weekend GPU change, key uniqueness, a beta by numpy least squares, a group mean). A failure stops `run_all.py`. |
| 9 | Honest limits | **OK** | README section 8 (Threats), updated with this audit's findings. |
| 10 | You understand it | **Not yet** | Every teammate still needs to walk through steps 00–06 and `app.py` before v1. |
