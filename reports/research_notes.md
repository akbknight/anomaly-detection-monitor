# Research Notes

## FRED Data Quality and Seasonal Adjustment

### Seasonal Adjustment Methodology

Both UNRATE and CPIAUCSL are seasonally adjusted by the U.S. Bureau of Labor Statistics (BLS) before release to FRED. The BLS uses the X-13ARIMA-SEATS method developed by the U.S. Census Bureau. Key properties:

- X-13ARIMA-SEATS removes predictable within-year patterns (e.g., summer hiring, holiday retail effects) using a combination of ARIMA modeling and moving-average filters.
- Seasonal factors are revised annually, which means historical FRED values are sometimes revised backward. For this monitoring use case, revisions are small enough (typically < 0.1 percentage point for UNRATE) to be negligible.
- CPIAUCSL seasonal adjustment accounts for regular price patterns in categories like energy (seasonal price cycles), apparel (end-of-season sales), and food (agricultural seasonality).

### Data Availability and Coverage

- UNRATE: Available from January 1948. 100% monthly coverage; no gaps in the 2000–present window.
- CPIAUCSL: Available from January 1947. 100% monthly coverage; no gaps in the 2000–present window.
- Missing values in the FRED CSV are encoded as the string `"."`. The `fetch_series()` function filters these before returning.

### Known Limitations

- Both series are subject to benchmark revisions. UNRATE is revised when BLS updates population controls (typically January of each year). Revisions are typically small.
- CPI methodology has been revised at various points (most significantly in 1998, which introduced the geometric mean formula to address substitution bias). Pre-1998 data is not directly comparable to post-1998 on a methodology-consistent basis — one reason this project starts in 2000.
- The FRED CSV endpoint does not require authentication but is subject to rate limiting. The `fred_client.py` module includes 3-attempt retry with 1-second backoff.

---

## Academic Background on CUSUM

### Page (1954) — Original Paper

E. S. Page, "Continuous Inspection Schemes," Biometrika, 41(1/2), pp. 100–115, 1954.

Page introduced the CUSUM chart as a sequential probability ratio test for detecting a shift in the mean of a normally distributed process. The key insight was that by accumulating deviations from a target value, the chart could detect small persistent shifts far more efficiently than Shewhart-type control charts, which only use the most recent observation.

The two key parameters are:
- k (reference value / slack): the magnitude of shift the chart is optimally designed to detect, typically set to half the expected shift size.
- h (decision interval): the threshold at which an alarm is raised. Selected to achieve a target ARL (Average Run Length) under the null hypothesis of no process shift.

### Montgomery (2012) — Industrial SPC Reference

Douglas Montgomery, "Introduction to Statistical Quality Control," 7th edition, Wiley, 2012.

Chapters 9–10 cover CUSUM design in detail. Key points relevant to this implementation:
- The "standardized" CUSUM uses k = 0.5 * sigma (reference value) and h = 4–5 * sigma (alarm threshold) as a standard starting design point for detecting ~1-sigma process shifts.
- ARL at k = 0.5, h = 4.0: approximately 168 observations before a false alarm under the null; approximately 10.4 observations to detect a 1-sigma shift. This is a practical trade-off for a monthly monitoring series.
- The alarm-and-reset convention (resetting S+ and S- to zero after an alarm) is standard practice in industrial SPC and is adopted here to allow detection of subsequent events after the first alarm.

### CUSUM in Macroeconomic and Financial Data

The application of CUSUM-type tests to macroeconomic data has a long history in structural break detection literature:

- Ploberger and Krämer (1992) developed CUSUM tests for regression residuals to detect coefficient instability.
- Andrews (1993) extended this to unknown breakpoint tests.
- In the context of unemployment, CUSUM is appropriate because the rate exhibits distinct "regimes" separated by crisis events — the series does not randomly fluctuate around a single long-run mean, but rather transitions between different steady states (e.g., the ~4–5% pre-GFC regime vs. the elevated post-GFC regime vs. the COVID shock).

Operating CUSUM on first differences (as implemented here) is equivalent to testing for a change in the *drift* of the series, which aligns precisely with the economic interpretation: an anomaly is a period where unemployment is moving in one direction at an abnormal pace, not merely that it is at an unusual level.

---

## Why IQR and Z-Score Give Different Results for CPI

The CPI series (CPIAUCSL) exhibits a strong right skew over the 2000–2026 window. This is because:

1. CPI is an index level (not a rate of change), and the index has risen approximately from 172 in January 2000 to approximately 315 by early 2026 — nearly doubling. This upward trend makes the distribution highly asymmetric when viewed in levels.

2. The right tail of the distribution (high CPI values from 2021–2026) is much longer than the left tail (low CPI values from 2000–2005). This is characteristic of a trending process with limited downside variance.

**Consequence for Z-score:** Because Z-score uses the global mean and standard deviation, and the series trends upward, the global mean is pulled toward the center of the 26-year range. Early observations (2000–2010) tend to have *negative* z-scores (they are below the long-run mean), while later observations (2018–2026) tend to have moderately positive z-scores. The algorithm's ability to detect the *level* anomalies in CPI is structurally limited because CPI levels are not stationary.

**Consequence for IQR:** The IQR method uses Q1 and Q3 to construct fences. For a strongly trending series, Q1 and Q3 are both shifted toward the center of the upward trend. Values from the early 2000s (well below the trend midpoint) and from the 2021–2026 inflation surge (well above) are both further from the fences than Z-score would suggest. This is why IQR can flag the 2021–22 inflation period as anomalous even when the month-by-month Z-scores are not individually extreme.

**Practical implication:** For trending or skewed series like CPI, the CUSUM method (operating on first differences) is the most reliable primary detector, with IQR providing distribution-free confirmation. Z-score is more informative for the UNRATE series, which is mean-reverting over multi-decade windows.

---

## Anomaly Detection in Macroeconomic Data: Regime Changes vs. Outliers

A key conceptual distinction in macroeconomic monitoring is between:

**Point outliers:** A single observation that is extreme relative to the surrounding data. Example: April 2020 unemployment rate of 14.8%, which jumped from 4.4% in March in a single month due to COVID lockdowns. This is correctly flagged by Z-score (4.7σ) and IQR.

**Regime shifts / structural breaks:** A sustained change in the level or trend of a series. Example: the 2008–2009 unemployment rise from ~5% to ~10% over 18 months. No single month in this sequence is a 4.7σ outlier, but the accumulated directional movement is historically anomalous. CUSUM is the appropriate tool for this pattern.

**False positives from trends:** A naive anomaly detector applied to a trending series (like CPI levels) will flag every late observation as an anomaly simply because the series is at a historically high level. Operating on differences resolves this by asking "is this month's change extreme?" rather than "is this month's level extreme?"

This three-way taxonomy (point outliers, regime shifts, trend-related false positives) is why the monitor runs three algorithms: Z-score and IQR for point outliers, CUSUM for regime shifts, and the differencing transformation to suppress trend-related false positives in the CUSUM.
