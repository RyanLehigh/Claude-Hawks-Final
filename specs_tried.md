# Specifications tried

Every specification run on this project is listed here, including ones that
didn't make the slides. Each is run for **every** firm in the sample.

**Running total:** 3 specifications × 8 firms = **24 regressions**
(v0, FAKE GPU data only; no real Ornn data has been run yet).

All of them: OLS of the daily excess stock return on the regressors below,
Newey-West (HAC) standard errors with 5 lags. Code: `code/04_compute_betas.py`.

| ID | Date added | Data | Firms | Formula | Why |
|----|-----------|------|-------|---------|-----|
| S1_same_day | 2026-11-13 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + dgpu` | Main compute beta (seed method step 1) |
| S2_same_day_ff3 | 2026-11-13 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + smb + hml + dgpu` | Robustness: size and value factors |
| S3_lead_lag | 2026-11-13 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + dgpu_lag2 + dgpu_lag1 + dgpu + dgpu_lead1 + dgpu_lead2` | Does the GPU price lead or lag stocks? |

`dgpu` = daily log change in the H100 rental price on the trading-day calendar
(weekend moves roll into Monday). `dgpu_lagk` = the GPU change *k* trading days
before the stock return. `dgpu_leadk` = *k* days after.

## Placebo note

On FAKE data every true compute beta is 0. In S1, 1 of 8 firms (META, p = 0.019)
is "significant" at 5%, about what chance predicts. Keep this in mind when reading
the real results.
