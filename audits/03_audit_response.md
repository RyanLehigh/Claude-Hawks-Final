# Checkpoint 2 — Instructor Audit Response

## A1 — Missing STATUS.md

**Status: Fixed, with one item to verify.**

We added `STATUS.md` to our main branch. It covers our initial research question, data sources, methodology, and what we've completed since Checkpoint 1.

The Checkpoint 1 section was written based on our existing proposal and repository. We still need to check it against our original Checkpoint 1 submission.

**Evidence:** [`STATUS.md`](../STATUS.md), PR #6 (merge commit `1ff4672`).

## A2 — Missing Nasdaq/AI Factor Control

**Status: Fixed.**

We added S4, which uses QQQ as an additional control for broader technology-market movements:

`ret_rf ~ mkt_rf + qqq_rf + dgpu`

This helps us check whether a stock's compute beta is really associated with GPU rental prices or just broader movements in tech stocks. We added QQQ to our data collection, logged the specification, and ran it for the companies in our sample. The v1 results now use real Ornn data across 28 companies.

**Evidence:** `code/04_compute_betas.py`, `code/config.py`, `data/raw/pull_log.csv`, `specs_tried.md`, `outputs/betas_long.csv`.

## A3 — GPU Price Timing Assumption

**Status: Both timing versions added; exact publication timing is still not directly confirmed by Ornn.**

Our original model assumed that the daily GPU price was available before the stock market closed. We added an alternative timing regression because that assumption could introduce look-ahead bias.

After getting the real Ornn data, we found that the daily index is timestamped at midnight New York time and described as an average of hourly prices. Since a daily average can include prices from after the 4 p.m. stock market close, we now use **next-day timing** in our main v1 regressions and keep **same-day timing** as a robustness check.

This is based on the timestamps and documentation, not direct confirmation from Ornn. We also note that next-day timing can mix older information with newer information, so the timing limitation isn't fully solved.

**Evidence:** `code/config.py`, `code/02_load_gpu_prices.py`, `code/04_compute_betas.py`, `specs_tried.md`, `outputs/robustness_betas.csv`, `audits/02_self_audit.md`.

## A4 — Incorrect Course Number

**Status: Fixed.**

We corrected the README to say FIN 331 instead of FIN 377, including in the v1 branch before merging it.

**Evidence:** [`README.md`](../README.md), PR #7.
