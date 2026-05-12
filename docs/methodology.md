# Methodology

## Data Sources

### Federal Reserve Bank of St. Louis (FRED)

All data is sourced from the Federal Reserve Bank of St. Louis Economic Data (FRED) public API. No API key is required; FRED serves public CSV exports at:

    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>

### UNRATE — U.S. Unemployment Rate

- **Full name:** Unemployment Rate (U-3), Seasonally Adjusted
- **Publisher:** U.S. Bureau of Labor Statistics (BLS)
- **Frequency:** Monthly
- **Units:** Percent
- **Seasonal adjustment:** Yes (X-13ARIMA-SEATS)
- **Available from:** January 1948
- **FRED URL:** https://fred.stlouisfed.org/series/UNRATE

The U-3 rate measures the share of the civilian labor force that is unemployed and actively seeking work. It is the most widely cited headline unemployment figure. Seasonal adjustment removes predictable within-year fluctuations (e.g., summer hiring, December retail peaks) to expose underlying cyclical and structural trends.

### CPIAUCSL — Consumer Price Index for All Urban Consumers

- **Full name:** Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
- **Publisher:** U.S. Bureau of Labor Statistics (BLS)
- **Frequency:** Monthly
- **Units:** Index, 1982–84 = 100
- **Seasonal adjustment:** Yes
- **Available from:** January 1947
- **FRED URL:** https://fred.stlouisfed.org/series/CPIAUCSL

CPIAUCSL measures the average price level for a fixed basket of goods and services purchased by urban consumers. It is the primary U.S. inflation gauge. The index is expressed relative to an average level of 100 in the 1982–84 base period. Month-over-month and year-over-year changes in the index measure consumer price inflation.

### Time period

This analysis uses January 2000 – present (approximately 26 years). The 2000 start date is chosen because:
- Pre-2000 data involves a different CPI methodology revision (1998) and Y2K-era data quality issues.
- All major portfolio-relevant crises fall within the window: 2001 recession, 2008 Global Financial Crisis (GFC), 2020 COVID-19 shock, and the 2021–22 inflation acceleration.
- 26 years provides enough history for robust global statistics (mean, std, quantiles) without distorting them with pre-modern data regimes.

---

## Detection Algorithms

### 1. Z-Score Method

**Formula:**

    z_i = |x_i - mu| / sigma

where mu is the series mean and sigma is the series standard deviation over the full sample.

**Threshold:** z_i > 2.5

A threshold of 2.5 standard deviations corresponds to approximately 1.2% of observations under a normal distribution, covering ~98.8% of the density. This is more conservative than the common 2.0 threshold (which flags ~4.6%) and less extreme than 3.0 (which flags only ~0.27%).

**Severity classification:**
- low: 2.5 < z <= 3.0
- medium: 3.0 < z <= 3.5
- high: z > 3.5

**Use case:** Point outliers — months where the value is an extreme departure from the historical average. Most effective for the unemployment rate, which exhibits approximate stationarity around a slowly shifting long-run mean. Less effective for the CPI level, which trends persistently upward.

---

### 2. IQR Method (Interquartile Range)

**Computation:**

    Q1 = 25th percentile of the series
    Q3 = 75th percentile of the series
    IQR = Q3 - Q1

    lower_fence = Q1 - 2.0 * IQR
    upper_fence = Q3 + 2.0 * IQR

Any observation outside [lower_fence, upper_fence] is flagged.

**Multiplier choice:** The classical Tukey (1977) fence uses 1.5. This project uses 2.0 as a more conservative setting appropriate for macroeconomic data, where heavy tails and multi-year regime shifts are expected features rather than measurement errors.

**Severity scoring:**

    dist = max(|val - lower_fence|, |val - upper_fence|) / IQR

- low: dist <= 1.5
- medium: 1.5 < dist <= 3.0
- high: dist > 3.0

**Use case:** Distribution-free outlier detection. Makes no assumption of normality. Particularly valuable for the CPI series, which is right-skewed (inflation can persist at elevated levels for extended periods, producing a longer upper tail). IQR is robust to heavy tails where Z-score can underestimate extremity.

---

### 3. CUSUM — Cumulative Sum Control Chart

**Algorithm:** Page's (1954) two-sided CUSUM chart applied to first differences.

**Preprocessing — operating on differences:**

The raw series levels (unemployment rate, CPI) have natural means that shift across economic cycles. Applying CUSUM to raw levels would produce alarms continuously as the series drifts between regimes. By differencing first:

    d_t = x_t - x_{t-1}    (month-over-month change)

the input to CUSUM is approximately stationary with near-zero mean, isolating structural breaks from secular trends.

**Accumulator update equations:**

    S+_t = max(0,  S+_{t-1} + d_t - mu_d - k)    [upward shift detector]
    S-_t = max(0,  S-_{t-1} - d_t + mu_d - k)    [downward shift detector]

where:
- mu_d = mean of first differences
- sigma_d = standard deviation of first differences
- k = 0.5 * sigma_d   (slack / reference value)
- h = 4.0 * sigma_d   (alarm threshold)

**Alarm:** fires when S+_t > h or S-_t > h. On alarm, both accumulators reset to zero and the alarm flag is set. The flag clears only when both accumulators fall back below h, preventing double-counting within a single event.

**Slack parameter k = 0.5 * sigma_d:**
The reference value controls sensitivity. Setting k = 0.5 * sigma is the standard recommendation in statistical process control literature (Montgomery, 2012). It optimally detects a shift of 1 sigma in the process mean. Too small a k increases false alarms; too large a k slows detection.

**Threshold h = 4 * sigma_d:**
Calibrated to produce approximately 1 false alarm per 200 observations at the expected noise level (consistent with ARL analysis in Montgomery 2012, Table 9.2). For a 26-year monthly series (~314 observations), this implies fewer than 2 expected false alarms over the full sample.

**Use case:** Sustained directional regime shifts — events that accumulate over multiple months and would be missed by point-based methods. Examples: the 2020 COVID unemployment ramp (rapid sequential monthly increases), the 2008 GFC deflation sequence, and the 2021–22 inflation acceleration.

---

## Deduplication

When multiple algorithms flag the same calendar month, three separate entries would over-represent the event. The deduplication step collapses all detections on the same date to a single entry using a priority rule:

    priority: high (3) > medium (2) > low (1)

The highest-severity detection is retained. After deduplication, results are sorted chronologically.

---

## Key Economic Events Captured

The 26-year window (2000–present) encompasses the following statistically significant periods:

| Period | Event | Series Affected |
|---|---|---|
| 2001 Q1–Q4 | Dot-com recession, 9/11 | UNRATE |
| 2008–2009 | Global Financial Crisis | UNRATE, CPI |
| 2009 Q2–Q4 | GFC deflation trough | CPI (CUSUM) |
| 2015 H2 | Oil price disinflation | CPI |
| Apr 2020 | COVID-19 shock, 14.8% unemployment | UNRATE (all three methods) |
| 2021–2022 | Post-COVID inflation acceleration | CPI (CUSUM, IQR) |
