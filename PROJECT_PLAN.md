# Project Plan — Anomaly Detection Monitor v1.0

## Objective

Upgrade the single-file `detect.py` script into a production-grade Python package with modular src/ layout, full documentation, unit tests, and proper project scaffolding.

## Completed work

### Phase 1 — Modularization

- [x] Extract `fetch_series()` into `src/data/fred_client.py` with retry logic (3 attempts, 1s backoff)
- [x] Extract `detect_zscore()` into `src/detectors/zscore.py` with full type hints and docstring
- [x] Extract `detect_iqr()` into `src/detectors/iqr.py` with full type hints and docstring
- [x] Extract `detect_cusum()` into `src/detectors/cusum.py` with full type hints and detailed algorithm docstring
- [x] Export all three detectors from `src/detectors/__init__.py`
- [x] Extract `process_series()` and `deduplicate_anomalies()` into `src/pipeline/runner.py`
- [x] Create `src/cli/run.py` as canonical entry point with SERIES config and `main()`
- [x] Reduce root `detect.py` to a one-line shim calling `src.cli.run:main`

### Phase 2 — Project scaffolding

- [x] `pyproject.toml` — build system, project metadata, console_scripts entry point
- [x] `requirements.txt` — pinned minimum versions for pandas, numpy, scipy
- [x] `Makefile` — run, test, clean targets
- [x] `.gitignore` — standard Python ignores

### Phase 3 — Data organization

- [x] Created `data/artifacts/anomaly_data.json` — archival copy of output
- [x] Created `data/raw/` and `data/interim/` with `.gitkeep` placeholder files
- [x] `src/pipeline/runner.py` writes to both root `anomaly_data.json` AND `data/artifacts/anomaly_data.json`
- [x] Root `anomaly_data.json` retained for index.html dashboard compatibility

### Phase 4 — Configuration

- [x] `configs/app/config.yaml` — series definitions, detection parameters, output paths

### Phase 5 — Documentation

- [x] `docs/methodology.md` — data sources, algorithm formulas, parameter choices
- [x] `docs/architecture.md` — data flow, module diagram, deployment context
- [x] `docs/decision_log.md` — 7 key design decisions with full rationale
- [x] `docs/data_dictionary.md` — complete field reference for anomaly_data.json

### Phase 6 — Reports

- [x] `reports/research_notes.md` — FRED data quality, CUSUM literature, IQR vs Z-score analysis
- [x] `reports/results.md` — documented anomaly findings with event narratives

### Phase 7 — Tests

- [x] `tests/test_detectors.py` — 5 tests each for Z-score, IQR, CUSUM (15 total)
- [x] `tests/test_pipeline.py` — 8 tests for deduplicate_anomalies()

### Phase 8 — Cleanup

- [x] Deleted `egypt_vs_india_README.md` (stray file from another project)

### Phase 9 — README

- [x] Upgraded README.md to professional production standard

## Directory structure after upgrade

```
anomaly-detection-monitor/
├── src/
│   ├── data/fred_client.py
│   ├── detectors/zscore.py, iqr.py, cusum.py, __init__.py
│   ├── pipeline/runner.py
│   └── cli/run.py
├── data/artifacts/, raw/, interim/
├── configs/app/config.yaml
├── docs/methodology.md, architecture.md, decision_log.md, data_dictionary.md
├── reports/research_notes.md, results.md
├── tests/test_detectors.py, test_pipeline.py
├── index.html          (unchanged — GitHub Pages dashboard)
├── anomaly_data.json   (root — required by dashboard)
├── detect.py           (shim)
├── pyproject.toml
├── requirements.txt
├── Makefile
└── .gitignore
```
