## 3. Methodology

Our project examines whether changes in GPU rental prices are associated with daily stock returns and whether this relationship differs across industries. We will use Python to combine GPU rental price data from Ornn, stock market data from Yahoo Finance, and market factor data from the Kenneth French Data Library.

### Data Preparation

We will first calculate daily stock returns and convert GPU rental prices into daily log changes. Using changes instead of absolute price levels helps prevent misleading relationships caused by long-term trends. We will then merge the datasets by trading date, creating a panel dataset where each observation represents one company on one trading day.

We will also verify that GPU price observations are correctly aligned with stock market closing times and account for weekends and market holidays.

### Regression Analysis

Our primary method will be ordinary least squares (OLS) regression. For each company, we will estimate the relationship between its daily excess stock return, overall market movements, and changes in GPU rental prices.

The regression model is:

**Excess Stock Return = Alpha + Market Beta × Market Excess Return + Compute Beta × GPU Price Change + Error**

The main coefficient of interest is the **compute beta**, which measures how sensitive a company's stock returns are to changes in GPU rental prices after controlling for general market movements.

We will use heteroskedasticity and autocorrelation consistent (HAC) standard errors to account for potential volatility and time dependence in daily financial data.

### Lead-Lag Analysis

We will also investigate whether GPU rental price changes occur before or after stock price movements. Our initial model examines GPU price changes up to two trading days before and after each stock return.

This allows us to test whether stock prices respond to compute price changes with a delay or whether the two variables move together because of broader market conditions.

### Industry Comparisons

We will compare compute betas across four groups:

1. **Chipmakers:** Companies such as NVIDIA and AMD.
2. **Cloud Providers:** Companies such as Microsoft and Amazon.
3. **AI-Heavy Software:** Companies such as Meta and Palantir.
4. **Control Group:** Companies with limited direct GPU exposure, such as Coca-Cola and Procter & Gamble.

Our initial prototype includes eight companies, with plans to expand to approximately 30 firms.

We will also test additional market factors to determine whether the estimated GPU exposure reflects a relationship with compute costs rather than general technology-sector movements.

Finally, we will present our findings through an interactive Streamlit dashboard that allows users to compare company-level compute betas, confidence intervals, industry groups, and lead-lag relationships.

## 4. Threats and Checks

Although our analysis aims to identify companies with meaningful exposure to GPU rental prices, several limitations could affect the reliability of our findings. We will address these issues through additional data validation, alternative regression specifications, and transparent reporting.

### GPU Price Timing and Look-Ahead Bias

One concern is whether GPU rental prices are recorded before or after the stock market closes. If a GPU price is recorded after 4:00 p.m. Eastern Time but matched with that day's stock return, our analysis could unintentionally incorporate information that investors did not yet have.

We plan to confirm the timing of Ornn's price observations and adjust the trading-day alignment when necessary. We will also examine how weekends and market holidays affect the data.

### Multiple Testing and False Positives

Because we plan to estimate regressions for approximately 30 companies across multiple specifications, some statistically significant relationships could arise by chance.

Our initial prototype demonstrates this risk. Even with simulated GPU data containing no true compute exposure, one of eight companies produced a statistically significant result at the 5% level.

To address this issue, we will maintain a record of all tested specifications in `specs_tried.md`, apply a multiple-testing adjustment such as the Holm correction, and report results across the entire sample rather than selecting only significant findings.

### Control Group and Industry Differences

Our control group includes companies with limited direct exposure to GPU costs, such as Coca-Cola and Procter & Gamble.

However, these companies may have lower stock market volatility than technology companies, making direct comparisons potentially misleading.

We plan to report standardized compute betas and consider expanding the control group to include companies with more comparable market risk.

### Omitted Variables and Broader Market Trends

GPU rental prices and technology stock returns may both respond to changes in AI investment, investor sentiment, or overall technology-sector performance.

This could create a statistical relationship even if GPU prices are not directly influencing stock returns.

Our current robustness specification includes the Fama-French size and value factors. We plan to add technology-sector controls, such as the return difference between QQQ and SPY, to examine whether compute beta is capturing broader technology-market movements.

### Sample Selection and Data Limitations

Our initial company classifications are based on current knowledge of which businesses are involved in AI, creating potential hindsight bias.

We plan to finalize the company list before analyzing real GPU price data to reduce the risk of selecting companies based on favorable results.

Additionally, our approximately two-year sample may not capture relationships across different economic conditions. We will disclose this limitation and avoid interpreting statistical correlations as proof of causation.

We will also examine missing or stale GPU price observations, since carrying forward outdated prices could distort the estimated relationships.

### Reproducibility and Data Privacy

Ornn's GPU rental price data is private and cannot be published in our GitHub repository.

To make the analysis reproducible without exposing proprietary information, our repository includes a simulated dataset with the same expected structure and a Python pipeline that rebuilds the regression outputs.

Our current dashboard uses simulated GPU data, so its results should not be interpreted as real economic findings.

Once the actual Ornn data becomes available, we will run the analysis using real observations while ensuring that proprietary price information remains private. The public dashboard will display derived results rather than raw GPU rental prices.
