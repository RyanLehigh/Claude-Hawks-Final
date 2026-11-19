# Project Status — Which Stocks Are Exposed to GPU Prices?

## 1. Checkpoint 1 — Initial Progress

For our FIN 331 final project, we wanted to examine whether changes in GPU rental prices are related to stock returns, especially for companies involved in AI computing. Our main research question is which companies' share prices are most exposed to the cost of compute. We also wanted to see whether GPU prices and stock returns move together on the same day, whether one moves before the other, and whether the relationship differs across industries.

To begin, we identified three main data sources. We planned to use Yahoo Finance for historical stock prices, the Kenneth French Data Library for market returns and risk-free rates, and Ornn for H100 GPU rental prices. We also decided to divide companies into four groups: chipmakers, cloud providers, AI-heavy software companies, and control companies. This would allow us to compare businesses that have different levels of exposure to GPU computing.

Our initial approach was to calculate daily stock returns and changes in GPU rental prices, match the observations by trading date, and use Ordinary Least Squares (OLS) regression to estimate a compute beta for each company. The compute beta would help us measure how a company's stock returns move in relation to GPU rental prices while accounting for broader market movements.

*Note: This section summarizes our initial project approach based on the current proposal and repository. We still need to confirm it against our original Checkpoint 1 submission.*

## 2. Current Progress — Checkpoint 2

Since our initial project stage, we have built a working Python pipeline that collects stock prices, prepares the data, runs regressions, and produces results for our dashboard. Our current sample includes eight companies across four groups:

| Group | Companies |
|---|---|
| Chipmakers | NVIDIA (NVDA), AMD |
| Cloud Providers | Microsoft (MSFT), Amazon (AMZN) |
| AI-Heavy Software | Meta (META), Palantir (PLTR) |
| Controls | Coca-Cola (KO), Procter & Gamble (PG) |

Our sample covers November 4, 2024, through September 30, 2026, with 477 trading days. We have already collected stock data from Yahoo Finance and market factors from the Kenneth French Data Library. However, we are still using simulated H100 rental prices because we have not yet incorporated the actual Ornn data. These simulated prices allow us to test whether our code works, but they cannot tell us whether GPU prices are actually related to stock returns.

After preparing the data, we ran OLS regressions to calculate compute betas for each company. We started with three specifications. The first examines the same-day relationship between GPU price changes and stock returns while controlling for market returns. The second adds the Fama-French size and value factors, and the third examines whether GPU price changes lead or lag stock returns by up to two trading days. We also use Newey-West standard errors with five lags to account for possible correlation in daily regression errors.

We have also created a Streamlit dashboard to organize our results and make them easier to understand. The dashboard allows us to compare compute betas across companies and examine how the relationships differ between groups.

**Dashboard:** https://claude-hawks-final-bcfmmhexdwvlz3ekklhhk9.streamlit.app/

## 3. Instructor Audit and Updates

After completing our initial pipeline, we received feedback from our instructor's Checkpoint 2 audit. The audit confirmed that our original pipeline could run from a fresh copy of the repository and independently reproduced our compute beta calculations and Newey-West standard errors. However, it also identified several areas we needed to improve.

One issue was that our regressions did not include a separate technology-market factor. For example, NVIDIA's stock and GPU rental prices could both increase because investors are becoming more optimistic about AI, rather than because GPU rental prices directly affect NVIDIA. To address this, we added a fourth regression using QQQ, an ETF that tracks the Nasdaq-100, as an additional control. This allows us to examine whether the compute beta changes after accounting for broader technology-market movements.

Another issue involved the timing of GPU rental prices. Our original model assumed that Ornn's daily GPU price was available before the stock market closed at 4:00 p.m. However, we have not confirmed the exact time Ornn records its prices. We therefore added a fifth regression that assumes the GPU price becomes available after the market closes and is matched to the next trading day. This gives us a way to compare both timing assumptions until we receive confirmation from Ornn.

With these two additional specifications, our pipeline now runs five regressions for each of our eight companies, giving us 40 regressions in total. We have also updated our specifications log and regression outputs to include the new models.

The audit also identified missing project documentation and an incorrect course number in our README. We are addressing these separately as part of our final audit response.

## 4. Remaining Work

Although our pipeline and dashboard are working, we still have several things to complete before the final presentation.

Our biggest priority is obtaining and incorporating the actual Ornn GPU rental price data. Right now, the simulated prices help us test the code, but we cannot draw meaningful conclusions about compute exposure from them. Once we receive the real data, we will need to check its format, confirm when the daily prices are recorded, and make sure the GPU observations are correctly matched with stock returns.

We also plan to expand our sample from eight companies to approximately 30 companies. This would allow us to compare more businesses within each group and see whether our findings are consistent across different industries. For example, instead of looking at only NVIDIA and AMD as chipmakers, we could include additional semiconductor companies to better understand how GPU price changes relate to their stock returns.

Another priority is improving our robustness checks. Since we are running multiple regressions, there is a possibility of finding statistically significant results simply by chance. We already saw this with our simulated data, where META had a significant result even though the GPU prices were generated independently of stock returns. We plan to account for multiple testing when analyzing the real data and examine whether our results remain consistent under different assumptions.

Finally, we will update our dashboard with the completed analysis and prepare our final presentation. We want to focus on explaining what the compute betas mean, how they differ across companies, and whether GPU rental prices provide useful information beyond broader market movements.

## 5. Overall Project Status

Overall, our project has progressed from an initial research question and methodology into a working analysis pipeline and dashboard. We have collected stock and market data, built our regression models, tested our calculations, and addressed the main technical issues identified in our instructor's audit.

Our next step is to incorporate actual Ornn GPU rental prices, expand our company sample, and evaluate whether the relationships we find are statistically and economically meaningful. Until then, our current results should be viewed as a proof of concept rather than evidence of actual GPU price exposure.
