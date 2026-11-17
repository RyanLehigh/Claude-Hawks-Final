# Specifications tried

Every specification run on this project is listed here, including ones that
didn't make the slides. Each is run for **every** firm in the sample.

**Running total:** 5 specifications × 8 firms = **40 regressions**
(FAKE GPU data only; no real Ornn data has been run yet).

S4 and S5 were added in response to the instructor audit (A2, A3), and both
were logged here *before* any real Ornn data was run.

All of them: OLS of the daily excess stock return on the regressors below,
Newey-West (HAC) standard errors with 5 lags. Code: `code/04_compute_betas.py`.

| ID | Date added | Data | Firms | Formula | Why |
|----|-----------|------|-------|---------|-----|
| S1_same_day | 2026-11-13 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + dgpu` | Main compute beta (seed method step 1) |
| S2_same_day_ff3 | 2026-11-13 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + smb + hml + dgpu` | Robustness: size and value factors |
| S3_lead_lag | 2026-11-13 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + dgpu_lag2 + dgpu_lag1 + dgpu + dgpu_lead1 + dgpu_lead2` | Does the GPU price lead or lag stocks? |
| S4_nasdaq | 2026-11-17 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + qqq_rf + dgpu` | Audit A2: is the compute beta just a Nasdaq/AI-sentiment beta? |
| S5_next_day | 2026-11-17 | FAKE | 8 (v0) | `ret_rf ~ mkt_rf + dgpu_nd` | Audit A3: same as S1 but with the other GPU timing rule (price set after the close) |

`dgpu` = daily log change in the H100 rental price on the trading-day calendar
(weekend moves roll into Monday), assuming a price dated *d* is known by the
4 pm ET close on *d*. `dgpu_nd` = the same change assuming the price dated *d*
is set after the close, so it is first known at the close of *d* + 1 day
(Monday uses Sunday's price, Friday uses Thursday's). `dgpu_lagk` = the GPU
change *k* trading days before the stock return; `dgpu_leadk` = *k* days after.
`qqq_rf` = QQQ daily return minus the risk-free rate.

**Which timing is the main spec:** S1 (same day) for now, but this is *not*
confirmed. Once Ornn tells us when each daily price is set, the matching
mapping becomes the main specification and the other stays logged here.

## Placebo note

On FAKE data every true compute beta is 0. In S1, 1 of 8 firms (META, p = 0.019)
is "significant" at 5%, about what chance predicts. Keep this in mind when reading
the real results.

Under S5 (other timing), 3 of 8 FAKE compute betas change sign relative to S1
(MSFT, AMZN, PG), and META goes from −0.134 to −0.012. These match the
instructor audit's independent re-estimate. So on this data, the same-day
result depends on the timing assumption.
