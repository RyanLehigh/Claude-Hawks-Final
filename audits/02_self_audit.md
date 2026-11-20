# Self-audit 02: Checkpoint 4 (v1)

**Date:** 2026-11-20 · **Branch:** `v1-results` · **Data:** real Ornn H100 SXM daily index (API), 28 firms

**How this was run:** a skeptical review in the spirit of the Quick Reference
*Skeptical review* prompt (#5), worked through the 11 checks in
`reference/project_rules.md`. Findings were tested against the code and data,
not just read off the code.

**Caveat on independence:** the same Claude Code session that wrote the v1 code
also ran this review. A teammate should rerun the *Skeptical review* prompt in a
fresh session before the PR is merged and add anything new below.

---

## 1. Findings, ranked by severity

| # | Severity | Finding | Status | Evidence |
|---|----------|---------|--------|----------|
| 1 | High | **GPU timing (open since v0, #1).** If the daily value dated *d* contains after-close hours, the v0 same-day regression has look-ahead. | **Addressed; inferred, not confirmed by Ornn.** Every daily value is stamped at midnight New York time (04:00/05:00 UTC), and Ornn's docs describe an hourly index averaged to a daily value. At 14:52 NY on 2026-11-20 the API's latest value was stamped 2026-11-19, with none for 11-20, so a day's value appears only after that day ends. v1 makes **next-day** timing the main spec (S1–S4) and keeps same-day as S5. | `code/00b_get_ornn.py`, `code/config.py` (`GPU_TIMING_*`), API probe 2026-11-20 19:52 UTC. Hand checks confirm `dgpu` = next-day column. |
| 2 | Medium | **Next-day timing is partly stale.** The value dated *d* averages all of day *d*, including hours 0:00–16:00 that already affected day *d*'s stock return. Counting it on *d* + 1 mixes old and new information, which biases betas **toward zero** (it can hide exposure, not create it). | **Real, disclosed.** No fix without hourly data (Ornn's Full tier). | README §8 Timing. |
| 3 | Medium | **Committed results can't be reproduced without a key.** `outputs/` holds real-data results; an auditor without an Ornn key reruns on the fake file and gets different numbers. | **Real, disclosed; unavoidable under Ornn's terms.** Tested: with `data/raw/ornn/` removed, `run_all.py` runs end to end on the fake file (28 firms, 140 regressions, all checks pass). With the real file, a rebuild reproduces every committed output byte for byte. | Runs on 2026-11-20; `git status` clean after the real rebuild. |
| 4 | Medium | **Multiple testing (v0 #3).** 28 firms × 5 specs. | **Fixed.** Benjamini-Hochberg p-values (`p_bh`) for S1: smallest is 0.53, so no firm survives. 2 of 28 firms pass p < 0.05 unadjusted (≈1.4 expected by chance). In S3, 6 of 140 lead/lag GPU terms pass p < 0.05 (7 expected by chance). | `outputs/compute_betas.csv`, `outputs/betas_long.csv`. |
| 5 | Medium | **Group test was a plain average (v0 plan).** A t-test across firm betas would treat 28 regressions on the *same* GPU series as independent. | **Fixed.** S6: group-minus-control equal-weighted portfolio regressed on market and GPU change, HAC SEs. AI-heavy software +0.044 (p = 0.087), cloud +0.020 (p = 0.42), chipmakers −0.006 (p = 0.85). | `code/04b_group_tests.py`, `outputs/group_tests.csv`. Hand-checked with a plain loop + numpy. |
| 6 | Medium | **S6 was pre-registered after the firm-level results were seen.** The firm list, timing, and S1–S5 were committed before any real-data run (commit `b1f891f`), but S6 and the BH correction were logged (commit `7781f62`) after S1 results were printed. | **Real, disclosed here.** Mitigation: both were promised in the proposal and README before any real data (method step 5; v0 audit plan for #3), and S6 was run once, as logged. | `git log`; `specs_tried.md`. |
| 7 | Medium | **Control group barely moves with the market (v0 #4).** KO, JNJ, PG, PEP, DUK market betas are −0.10 to 0.07. | **Checked: real, not a bug.** Raw prices show no date shift (corr with SPY ≈ 0 at lags −1, 0, +1), controls correlate 0.4–0.6 with each other, and on the 2025-04-03 tariff shock SPY fell 4.9% while KO, JNJ, DUK rose 2.6–3.0%. Volatility-scaled betas (`std_compute_beta`) give the same group ranking. | README §8; `outputs/group_summary.csv` (`mean_std_compute_beta`). |
| 8 | Medium | **Firm selection uses hindsight (v0 #5).** | **Partly addressed.** The 28-firm list and groups were in the README at Checkpoint 2 (commit `72122b2`, before any real data) and used unchanged. It is still a 2026 view of "AI stocks". | `git show 72122b2:README.md`. |
| 9 | Low | **Sample ends 2026-09-30, not 2026-11-19.** Ken French daily factors stop there, so the inner merge drops 36 trading days (1,008 firm-days) of available stock and GPU data. | **Real, disclosed.** Rerun with `--refresh` once Ken French updates. | Step 3 log: "Ken French factors (m:1): 17,127 -> 16,119". |
| 10 | Low | **GPU volatility is recoverable from public outputs.** `sd(dgpu) = std_compute_beta × sd(stock return) / compute_beta`, and stock returns are public. That reveals one summary statistic of Ornn's series (not the price path). | **Real, low risk.** The price path and daily changes stay private; `data/processed/` and hand-check GPU values are never committed. Drop `std_compute_beta` from `outputs/` if the professor considers this too much. | `code/04_compute_betas.py`. |
| 11 | Low | **CRWV has a shorter sample** (listed 2025-03-28): 378 days vs 569. | **Real, handled.** Estimated on its own days, reported with `nobs`; enters group portfolios only when it trades. | `outputs/compute_betas.csv`. |
| 12 | Low | **`--refresh` can move numbers** (yfinance revises adjusted prices). | **Handled.** Default run uses committed raw files; `data/raw/pull_log.csv` records each pull (stocks, factors, Ornn API). | `data/raw/pull_log.csv`. |
| — | Checked, clean | **Merges:** every merge uses `validate=`; drops are printed. New merges in step 4 and 5 use `validate="1:1"`. | — | `code/03`–`05`. |
| — | Checked, clean | **Private data and keys:** `data/raw/ornn/`, `data/processed/`, `env/.env` are git-ignored; staged files checked before each commit. The API key is read from `env/.env` and never printed or logged. | — | `.gitignore`, `code/00b_get_ornn.py`. |
| — | Checked, clean | **LLM leakage (rule 5):** no LLM is used anywhere in the pipeline or the results. | Not applicable. | — |
| — | Checked, clean | **Hand checks (rule 8):** 17 checks, one or more per step, including the new BH, scaled-beta and S6 numbers. All pass on real and fake data. | — | `outputs/hand_checks.txt`. |

## 2. Still open

| # | Issue | Plan |
|---|-------|------|
| 1–2 | Timing is inferred; next-day is partly stale | Disclosed. If hourly data becomes available, rebuild the GPU change from 16:00-to-16:00 NY windows. |
| 6 | S6 logged after firm results were seen | Disclosed; no further specs to be added without logging first. |
| 8 | Hindsight in "AI stock" groups | Disclosed. Optional: a placebo group of non-AI tech firms. |
| 9 | Sample ends 2026-09-30 | `python run_all.py --refresh` before the final presentation if Ken French has updated. |
| — | Short sample (one regime, ~2 years) | Disclosed in README §8; optional subperiod split (2024–25 vs 2026) would need logging in `specs_tried.md` first. |
