# Economic Anomaly Detection Monitor

Real-time statistical monitoring of U.S. macroeconomic indicators, applying three independent anomaly detection algorithms to flag structural breaks and regime shifts in Federal Reserve (FRED) data. Live dashboard at [akbknight.github.io/anomaly-detection-monitor](https://akbknight.github.io/anomaly-detection-monitor/).

## What this project does

This project applies statistical process control to two core FRED series — U.S. Unemployment Rate (UNRATE) and Consumer Price Index (CPIAUCSL) — and independently runs three anomaly detection algorithms to surface significant deviations that a human analyst or automated monitoring system would need to investigate.

The dashboard answers a concrete operational question: given 26 years of macroeconomic data, which months represent genuine statistical anomalies, and how severe are they? The results include the COVID-19 unemployment shock (April 2020: 14.8%, 4.7σ), the 2008 GFC deflation (CUSUM 8.9σ), the 2015 oil-price disinflation, and the 2021–2022 inflation acceleration sequence.

## Key results

| Series | Anomalies | High | Most Significant Event |
|---|---|---|---|
| UNRATE | 4 | 3 | April 2020 — 14.8% (Z-score: 4.73σ) |
| CPI | 7 | 1 | Nov 2008 — GFC deflation (CUSUM: 8.9σ) |

## Detection algorithms

| Algorithm | Mechanism | Best for |
|---|---|---|
| **Z-Score** | Flags \|z\| > 2.5 standard deviations from the mean | Single-point outliers in stationary series |
| **IQR** | Flags values outside Q1−2×IQR or Q3+2×IQR | Distribution-free outlier confirmation |
| **CUSUM** | Cumulative sum control chart on first differences; resets on alarm | Sustained directional regime shifts |

The three algorithms are complementary: Z-score and IQR flag point outliers; CUSUM detects shifts that accumulate over multiple months and would be missed by point-based methods.

## Tech stack

| Layer | Technology |
|---|---|
| Data | FRED API / UNRATE, CPIAUCSL series |
| Analysis | Python 3, pandas, numpy, scipy.stats |
| Dashboard | Chart.js 4, plain HTML/CSS/JS |
| Deployment | GitHub Pages |

## How to run

```bash
git clone https://github.com/akbknight/anomaly-detection-monitor.git
cd anomaly-detection-monitor

pip install pandas numpy scipy

# Fetch fresh FRED data and rerun detection
python detect.py
# Outputs: anomaly_data.json (pre-embedded in index.html)

# Open index.html in browser — no build step required
```

**Requirements:** Python 3.9+. No API key needed — the script fetches public CSV data from `fred.stlouisfed.org`.

## Data source

**Federal Reserve Bank of St. Louis (FRED)**
- UNRATE — U.S. Unemployment Rate, Seasonally Adjusted: https://fred.stlouisfed.org/series/UNRATE
- CPIAUCSL — Consumer Price Index, All Items, Seasonally Adjusted: https://fred.stlouisfed.org/series/CPIAUCSL

License: Public domain.

## Methodology

The three algorithms operate independently and are applied to 314 months of data (Jan 2000 – Mar 2026):

**Z-Score:** Each observation is standardized against the full-series mean and standard deviation. Points exceeding 2.5σ are flagged. Effective for series with approximately normal distributions around a stable mean; less effective for trending series.

**IQR:** Computes Q1, Q3, and IQR across the full series. Flags values below Q1−2×IQR or above Q3+2×IQR. Distribution-free and robust to heavy tails. Used as confirmation for Z-score outliers.

**CUSUM on first differences:** Standard Page (1954) CUSUM chart applied to month-over-month changes rather than raw levels, eliminating the effect of long-run trends. Slack parameter k = 0.5σ; alarm threshold h = 4σ; resets to zero on alarm signal to allow detection of subsequent shifts. This approach successfully identifies the 2008 GFC deflation, 2015 oil disinflation, COVID shock, and the 2021–2022 inflation acceleration as distinct regime shifts.

Anomaly deduplication: where multiple algorithms flag the same month, the highest-severity detection is retained.

## Skills demonstrated

- **Statistical process control:** Z-score, IQR, and CUSUM algorithms with tuned sensitivity
- **Time-series analysis:** Regime shift detection vs. point anomaly detection
- **Operational monitoring:** Alarm + reset logic, severity triage, deduplication
- **Business interpretation:** Connecting statistical flags to real economic events
- **Data visualization:** Chart.js interactive dashboard with per-point anomaly markers, dark/light mode
- **Reproducible analysis:** Python script fetching fresh FRED data on every run

## Author

**Akshay Kumar**
[linkedin.com/in/akshaykumardl](https://www.linkedin.com/in/akshaykumardl/)
