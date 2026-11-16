# Instructor audit: Claude Hawks, Checkpoint 2

**Repo:** RyanLehigh/Claude-Hawks-Final · **Audited commit:** `72122b2` (2026-11-14, merge of PR #2 into `main`) · **Seed:** 15, compute costs: which stocks are exposed to GPU prices? (Ornn)

> Note from your human teacher: This review is generated with minimal supervision from Opus 5.5-high. It is thorough, but can be too generous at times and doesn't know my taste for what is "good". Grades it and I would assign are correlated, but noisy, ok? If you want additional feedback from _me_, you need to find me before/after/during class or during office hours for a guaranteed speedy reply. I will try to respond to emails and issues, but can not respond to student inquiries around the clock across the final weeks of class. Response times will be unpredictable, though during Thanksgiving week, I will do my best to respond quickly virtually, as in person options will be nil.

## Summary

A clean, reproducible v0. A fresh clone runs `run_all.py` in 11 seconds, rebuilds every table and the hand-check log identically, and your own hand checks pass. My independent code reproduces all 8 compute betas and Newey–West standard errors exactly. You follow the Ornn data rule carefully: no real Ornn file appears anywhere in the history, and you git-ignored `data/processed/` because GPU *changes* would rebuild the price path. Good catch. What needs work:
1. `STATUS.md` was never committed (A1).
2. Nothing yet separates a compute beta from a Nasdaq/AI factor (A2).
3. The GPU timing assumption moves the answer (A3).

| Check | Result |
|---|---|
| Reruns from scratch | ✅ exit 0, 11.0 s; `compute_betas.csv`, `betas_long.csv`, `group_summary.csv`, `sample_summary.csv`, `hand_checks.txt` identical |
| Inputs have provenance | ✅ `data/raw/pull_log.csv` and `data/README.md`. Ornn metadata is unknown, which you disclose |
| Keys unique, merges validated | ✅ `(ticker, date)` asserted, `validate=` |
| No look-ahead / survivorship | ⚠️ GPU timing assumed (A3). Firms picked with hindsight (disclosed) |
| LLM leakage handled | n/a |
| `specs_tried.md` complete | ✅ 3 specs × 8 firms, with a placebo note |
| Magnitudes discussed | ⚠️ `bps_per_10pct_gpu_move` is there, meaningless on FAKE data (fair) |
| Hand checks | ✅ `code/06_hand_checks.py`, which stops the run on failure |
| Threats to validity | ✅ README §8, unusually complete |
| Every number traces to `outputs/` | ✅ |

## What holds up

- **Independent recomputation.** My own code reads your committed `prices.csv`, `ff3_daily.csv` and `ornn_FAKE.csv`. It applies your stated rule (price dated d known by the close of d, last price on or before each trading day, log change) and fits OLS with Newey–West errors (Bartlett, 5 lags). It reproduces `outputs/compute_betas.csv` for all 8 firms (n = 477): largest difference 5e-16 in the beta, 2e-16 in the SE. Examples: META −0.1342 (SE 0.0573), PLTR +0.0732 (SE 0.1057).
- **Seed 15 items:**
  - **Changes, not levels:** yes, log changes.
  - **Weekend prices:** rolled into Monday, with a hand check on a Monday.
  - **Ranking many firms:** every firm is reported, groups are fixed in `config.py` beforehand, and you note the FAKE-data placebo (1 of 8 "significant").
  - **Reproducibility with private data:** a FAKE file with true beta = 0, and `data_source` stamped on every output.
- **Your control-group finding is real.** KO's market beta of −0.04 over 2024-11 to 2026-09 also shows up in another team's independently built panel. Your plan to standardize betas before comparing groups is the right response.

## Findings

### A1 · Major · `STATUS.md` was never committed

**Evidence:** No `STATUS.md` exists at `72122b2` or in any commit on any branch (`git log --all -- STATUS.md` is empty). README §7 lists `STATUS.md` as the Checkpoint 1 deliverable.

**Fix:** Add `STATUS.md`: the Checkpoint 1 memo plus a current-status update.

**How to show it's fixed:** The file exists on `main`.

### A2 · Major · No Nasdaq/AI factor control yet

**Evidence:** `code/04_compute_betas.py` S1 uses `mkt_rf` only, and S2 adds SMB and HML. README method step 6 and threat "Omitted factors" both name a Nasdaq/tech factor, but no specification includes one.

**Why it matters:** This is on the seed's audit list: "whether a compute beta is just an AI-sentiment or Nasdaq factor in disguise." With real Ornn data, AI stocks and GPU rental prices may both respond to AI news, and a market-only model would credit that to compute.

**Fix:** Add S4: `ret_rf ~ mkt_rf + qqq_rf + dgpu` (or an SMH/semiconductor excess return, or an equal-weighted basket of your AI firms excluding the firm itself). Pull QQQ/SMH in `01_get_returns.py`, log it in `pull_log.csv`, and add the row to `specs_tried.md` before running it on real data.

**How to show it's fixed:** `betas_long.csv` has S4 for every firm.

### A3 · Minor · The timing assumption changes the betas: plan to report both mappings

**Evidence:** `code/02_load_gpu_prices.py:5-8` assumes the GPU price dated d is known by the 4 pm ET close on d (disclosed; your self-audit #1). I re-estimated S1 with the other plausible rule, where a price dated d is set after the close and maps to the next trading day. **3 of 8 compute betas change sign** on the FAKE data (PG +0.022 → −0.010, MSFT −0.061 → +0.035, AMZN −0.092 → +0.031). META goes from −0.134 (your one "significant" firm) to −0.012.

**Why it matters:** Timing is on this seed's audit list. Until Ornn confirms the stamp time, the same-day beta's sign depends on an assumption.

**Fix:** Ask Ornn for the exact time and time zone of each daily print. Until then, compute both mappings and report both, labeled. Once the time is known, keep the correct one as the main specification and log the other in `specs_tried.md`.

**How to show it's fixed:** `config.py` holds the confirmed timestamp rule, and `betas_long.csv` has the alternative mapping as a labeled spec.

### A4 · Minor · Wrong course number in the README

**Evidence:** `README.md:3` says "FIN 377" (the course is FIN 331).

**Fix:** Correct the course number.

## How to respond

This audit is `audits/02_instructor_audit.md` in your repo. Fix what you can, then add `audits/03_audit_response.md`, replying to each finding ID: fixed (the commit), disputed (why), or disclosed as a limitation (where).

**Deadline: Saturday, November 21, 2026.**
