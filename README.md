# Economic Anomaly Detection Monitor

Statistical monitoring of U.S. macroeconomic indicators using three independent anomaly detection algorithms applied to Federal Reserve (FRED) data. Surfaces structural breaks and regime shifts in 26 years of unemployment and inflation data.

Live dashboard: [akbknight.github.io/anomaly-detection-monitor](https://akbknight.github.io/anomaly-detection-monitor/)

---

## What it detects

- **2 FRED series:** U.S. Unemployment Rate (UNRATE) and Consumer Price Index (CPIAUCSL)
- **3 detection algorithms:** Z-score, IQR, CUSUM — each tuned to a different anomaly profile
- **26 years of data:** January 2000 – present (~314 monthly observations per series)
- **Key events captured:** April 2020 COVID shock (14.8% unemployment, 4.73σ), November 2008 GFC deflation (CUSUM 8.9σ), 2021–22 inflation acceleration, 2015 oil disinflation

| Series | Unique Anomalies | High Severity | Most Significant Event |
|---|---|---|---|
| UNRATE | 4 | 3 | April 2020 — 14.8% unemployment (Z-score: 4.73σ) |
| CPI | 7 | 1 | November 2008 — GFC deflation (CUSUM: 8.9σ) |

---

## Quick start

```bash
git clone https://github.com/akbknight/anomaly-detection-monitor.git
cd anomaly-detection-monitor

pip install -r requirements.txt

# Fetch fresh FRED data and run all three detectors
python detect.py
# Outputs: anomaly_data.json

# Open index.html in any browser — no build step required
```

No API key required. FRED data is fetched from public CSV endpoints.

---

## How it works

1. **Fetch:** `src/data/fred_client.py` downloads UNRATE and CPIAUCSL from the FRED public CSV API with 3-attempt retry logic.
2. **Detect:** Three independent algorithms run on each series — Z-score, IQR, and CUSUM — each targeting a different anomaly type.
3. **Deduplicate:** `src/pipeline/runner.py` collapses multiple detections on the same date to the highest-severity finding.
4. **Output:** Results are written to `anomaly_data.json`, consumed by the Chart.js dashboard in `index.html`.

---

## Dashboard features

- Interactive time-series chart with per-point anomaly markers
- Severity color coding: high (red), medium (orange), low (yellow)
- Hover tooltips with algorithm, score, and description for each anomaly
- Toggle between UNRATE and CPI views
- Dark / light mode

---

## Detection algorithms

| Algorithm | Mechanism | Best for |
|---|---|---|
| **Z-Score** | Flags observations where \|x_i - mu\| / sigma > 2.5 | Single-point outliers; rapid shocks |
| **IQR** | Flags values outside Q1 - 2×IQR or Q3 + 2×IQR | Distribution-free outlier confirmation; right-skewed series |
| **CUSUM** | Page (1954) two-sided cumulative sum chart on first differences; k = 0.5σ, h = 4σ | Sustained directional regime shifts accumulating over multiple months |

The three algorithms are complementary: Z-score and IQR flag point outliers; CUSUM detects shifts that accumulate over multiple months and would be missed by point-based methods. See [docs/decision_log.md](docs/decision_log.md) for full parameter rationale.

---

## Data sources

- **UNRATE** — U.S. Unemployment Rate (U-3), Seasonally Adjusted, Monthly. Bureau of Labor Statistics via FRED.
  [https://fred.stlouisfed.org/series/UNRATE](https://fred.stlouisfed.org/series/UNRATE)
- **CPIAUCSL** — Consumer Price Index for All Urban Consumers, Seasonally Adjusted, Monthly. BLS via FRED.
  [https://fred.stlouisfed.org/series/CPIAUCSL](https://fred.stlouisfed.org/series/CPIAUCSL)

License: Public domain (U.S. government data).

---

## Methodology

Full statistical methodology: [docs/methodology.md](docs/methodology.md)

Key design decisions: [docs/decision_log.md](docs/decision_log.md)

Module architecture: [docs/architecture.md](docs/architecture.md)

Output format: [docs/data_dictionary.md](docs/data_dictionary.md)

---

## Technical stack

| Layer | Technology |
|---|---|
| Data ingestion | Python `urllib`, FRED public CSV API |
| Analysis | Python 3.10+, pandas 2.x, numpy 1.24+, scipy.stats |
| Anomaly detection | Z-score (scipy), IQR (pandas quantile), CUSUM (custom implementation) |
| Dashboard | Chart.js 4, plain HTML/CSS/JS — no build step |
| Deployment | GitHub Pages |
| Tests | pytest |
| Package | pyproject.toml, setuptools |

---

## Project structure

```
anomaly-detection-monitor/
├── src/
│   ├── data/fred_client.py       # FRED HTTP client with retry logic
│   ├── detectors/                # zscore.py, iqr.py, cusum.py
│   ├── pipeline/runner.py        # Orchestration and deduplication
│   └── cli/run.py                # Entry point
├── configs/app/config.yaml       # Series and detection parameters
├── docs/                         # Methodology, architecture, decisions
├── reports/                      # Research notes and results
├── tests/                        # 23 unit tests
├── data/artifacts/               # Archival output copies
├── index.html                    # Chart.js dashboard (GitHub Pages)
├── anomaly_data.json             # Output consumed by dashboard
└── detect.py                     # Root shim → src.cli.run:main
```

---

## Author

**Akshay Kumar**
[linkedin.com/in/akshaykumardl](https://www.linkedin.com/in/akshaykumardl/)
