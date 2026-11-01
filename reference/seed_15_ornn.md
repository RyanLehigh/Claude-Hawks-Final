# Seed 15: Compute Costs: Which Stocks Are Exposed to GPU Prices?

**Industry partner:** Ornn, a company that builds markets and price benchmarks
for GPU compute. Ornn will provide data and would be excited to read the
report, so this project is written for a real reader. Talk to the professor
first; they set up the data access.

## Research question

Which companies' share prices are most exposed to the cost of compute?

- Do GPU rental prices and stock returns move together on the same day?
- Do changes in compute prices **lead or lag** changes in stocks?

## Who would pay for the answer

- Ornn and its customers (anyone hedging compute costs)
- A portfolio manager sizing AI exposure
- A CFO whose margins depend on GPUs

## Unit of observation

- **Input row:** firm × day: stock return, market return, change in the GPU rental price.
- **Output row:** one per firm: compute beta, standard error, lead and lag
  coefficients, and group (chipmaker, cloud provider, AI-heavy software, no exposure).

## Data

| Source | What | Notes |
|--------|------|-------|
| Ornn (via professor) | ~2 years of daily GPU rental prices | Check which GPU models, regions, and rental terms are included. **Private.** |
| yfinance | Daily stock returns | Public |
| Ken French Data Library | Market and factor returns | Public |

### Data rule (Ornn data is private)

- Ornn's data is **never posted publicly**: not in the repo, not in the
  dashboard, not anywhere else.
- Keep the raw files out of git (list the folder in `.gitignore`) and get them
  from the professor.
- So the pipeline still runs for the auditors, commit a small **fake file**
  with the same columns (like `wacc_FAKE.csv` in the L15 template).
- The README must say the real data comes from Ornn through the professor.

## Method

1. Regress each firm's daily return on the market return and the change in
   the compute price. The coefficient on compute is the **compute beta**
   (same idea as L15's market beta).
2. Add leads and lags of the compute price change.
3. Compare across groups of firms.

## Dashboard

Pick a firm and see its compute beta with a confidence interval and its
lead-lag profile, next to a ranking of the most exposed firms.

## Minimum viable product (about two weeks)

- 30 firms in clear groups: chipmakers, cloud providers, AI-heavy software,
  and a control group with no compute exposure
- One GPU price series
- Two years of data
- Same-day compute betas

## Stretch goals

Ornn is open to other questions shaped around the team's interests and their data:

- How well GPU futures would hedge compute costs
- How auction and order-book market designs compare
- How differences across GPU models, regions, and rental terms affect building
  a benchmark price

## What the auditors will poke at

- **Spurious trends:** trends make any two series look related. Use changes, not levels.
- **Timing:** when is the day's GPU price set relative to the stock market
  close? GPU prices may exist on weekends (like bitcoin in Seed 14).
- **Multiple testing:** the "most exposed" of 100 firms looks exposed by
  chance. Log every firm and specification in `specs_tried.md`.
- **Omitted factors:** is the compute beta just an AI-sentiment or Nasdaq
  factor in disguise?
- **Short sample:** two years is one regime.
- **Reproducibility with private data:** see the data rule above.
