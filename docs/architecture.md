# Architecture

## Data Flow

```
FRED Public CSV API
        |
        v
src/data/fred_client.py
  fetch_series(series_id, start)
  - HTTP GET with 3-attempt retry (1s backoff)
  - Parse CSV, drop missing values (".")
  - Return date-indexed pd.Series from start date
        |
        v
src/detectors/
  detect_zscore(series)   --> list of anomaly dicts
  detect_iqr(series)      --> list of anomaly dicts
  detect_cusum(series)    --> list of anomaly dicts
        |
        v (combined list)
src/pipeline/runner.py
  deduplicate_anomalies()
  - Collapse same-date detections to highest severity
  - Sort chronologically
  process_series()
  - Orchestrates fetch + detect + dedup
  - Assembles structured result dict
        |
        v
anomaly_data.json (root)        <-- index.html dashboard reads this
data/artifacts/anomaly_data.json <-- archival copy
        |
        v
index.html
  Chart.js 4 interactive dashboard
  - Time-series chart with anomaly markers
  - Per-point tooltips with severity and description
  - Dark/light mode toggle
  Served via GitHub Pages at:
  https://akbknight.github.io/anomaly-detection-monitor/
```

## Module Diagram

```
anomaly-detection-monitor/
│
├── detect.py                    # Root shim → src.cli.run:main
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── fred_client.py       # FRED HTTP client + retry logic
│   │
│   ├── detectors/
│   │   ├── __init__.py          # Re-exports detect_zscore, detect_iqr, detect_cusum
│   │   ├── zscore.py            # Z-score anomaly detection
│   │   ├── iqr.py               # IQR anomaly detection
│   │   └── cusum.py             # CUSUM anomaly detection
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── runner.py            # Orchestration: process_series, deduplicate, write
│   │
│   └── cli/
│       ├── __init__.py
│       └── run.py               # Entry point: SERIES config + main()
│
├── configs/
│   └── app/
│       └── config.yaml          # Series + detection parameters (reference)
│
├── data/
│   ├── artifacts/
│   │   └── anomaly_data.json    # Archival output copy
│   ├── raw/                     # (placeholder for raw CSVs if caching added)
│   └── interim/                 # (placeholder for intermediate transforms)
│
├── docs/
│   ├── methodology.md           # Statistical methods in depth
│   ├── architecture.md          # This file
│   ├── decision_log.md          # Key design decisions with rationale
│   └── data_dictionary.md       # anomaly_data.json field reference
│
├── reports/
│   ├── research_notes.md        # Literature and data quality notes
│   └── results.md               # Documented anomaly findings
│
├── tests/
│   ├── __init__.py
│   ├── test_detectors.py        # Unit tests for all three detectors
│   └── test_pipeline.py         # Unit tests for deduplication logic
│
├── index.html                   # GitHub Pages dashboard (do not modify)
├── anomaly_data.json            # Root output — consumed by index.html
├── detect.py                    # Root shim for backwards compatibility
├── pyproject.toml               # Package metadata + console_scripts entry point
├── requirements.txt             # Pip-installable dependencies
├── Makefile                     # run / test / clean targets
└── .gitignore
```

## Why Three Algorithms

Each algorithm catches a fundamentally different anomaly profile. No single method covers all three patterns present in macroeconomic data:

| Algorithm | Anomaly type detected | Limitation |
|---|---|---|
| Z-score | Single-point magnitude outliers | Assumes normality; distorted by trends |
| IQR | Distribution-free point outliers | Does not detect sequential shifts |
| CUSUM | Sustained directional regime shifts | Does not flag isolated single-month spikes |

Using all three and deduplicating by severity provides comprehensive coverage:
- Z-score catches the April 2020 COVID spike (14.8% unemployment, 4.7σ)
- IQR provides distribution-free confirmation of the same event
- CUSUM catches the 2008 GFC deflation sequence and the 2021–22 inflation acceleration — events that accumulate over 3–6 months and would score unremarkably in any individual month

See `docs/decision_log.md` for full decision rationale.

## Deployment

The repository is configured for GitHub Pages, which serves `index.html` from the root. The dashboard reads `anomaly_data.json` relative to its own URL (i.e., from the repo root). Running `python detect.py` refreshes the root-level JSON, which — after a `git push` — updates the live dashboard.
