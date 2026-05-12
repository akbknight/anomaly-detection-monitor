# Data Dictionary — anomaly_data.json

Complete field reference for the JSON output produced by `detect.py` / `src/cli/run.py`.

---

## Top-level structure

```json
{
  "generated": "2026-05-12",
  "series": [ <SeriesResult>, <SeriesResult> ]
}
```

| Field | Type | Description |
|---|---|---|
| `generated` | string | ISO date (YYYY-MM-DD) when the file was produced. |
| `series` | array | One SeriesResult object per FRED series processed. Order matches SERIES config. |

---

## SeriesResult

```json
{
  "meta": { ... },
  "history": { ... },
  "anomalies": [ ... ],
  "counts": { ... }
}
```

### meta

Summary statistics for the series.

| Field | Type | Description |
|---|---|---|
| `id` | string | FRED series identifier. E.g., `"UNRATE"`, `"CPIAUCSL"`. |
| `name` | string | Human-readable series name. |
| `units` | string | Unit description. E.g., `"Percent (Seasonally Adjusted)"`. |
| `color` | string | Hex color code used in the dashboard chart. |
| `source` | string | Data provider name. Always `"Federal Reserve Bank of St. Louis (FRED)"`. |
| `source_url` | string | FRED series page URL. |
| `period` | string | Human-readable date range. E.g., `"Jan 2000 – Mar 2026"`. |
| `n_months` | integer | Total number of monthly observations in the series. |
| `latest_value` | float | Most recent observation value, rounded to 4 decimal places. |
| `latest_date` | string | Most recent observation date in long format. E.g., `"March 2026"`. |
| `mean` | float | Full-sample arithmetic mean, rounded to 4 decimal places. |
| `std` | float | Full-sample standard deviation, rounded to 4 decimal places. |

### history

Full time series for chart rendering.

| Field | Type | Description |
|---|---|---|
| `dates` | array of strings | ISO date strings (`"YYYY-MM-DD"`) for each observation. |
| `values` | array of floats | Corresponding observation values, rounded to 4 decimal places. Parallel array to `dates`. |

### anomalies

List of flagged observations, deduplicated (one entry per date, highest severity retained).

| Field | Type | Description |
|---|---|---|
| `date` | string | ISO date (`"YYYY-MM-DD"`) of the flagged observation. |
| `value` | float | Observed value at that date, rounded to 4 decimal places. |
| `type` | string | Detector that produced the surviving (highest-severity) flag. One of `"zscore"`, `"iqr"`, `"cusum"`. |
| `score` | float | Algorithm-specific severity score, rounded to 3 decimal places. For Z-score: |z|. For IQR: distance from fence in multiples of IQR. For CUSUM: S+/S- at alarm in multiples of sigma. |
| `severity` | string | Severity tier. One of `"low"`, `"medium"`, `"high"`. |
| `description` | string | Human-readable flag description including score and context. |

### counts

Summary of anomaly detection results.

| Field | Type | Description |
|---|---|---|
| `zscore` | integer | Number of anomalies flagged by Z-score before deduplication. |
| `iqr` | integer | Number of anomalies flagged by IQR before deduplication. |
| `cusum` | integer | Number of anomalies flagged by CUSUM before deduplication. |
| `total_unique` | integer | Number of unique dates flagged after deduplication. |
| `high` | integer | Number of deduplicated anomalies with severity `"high"`. |
| `medium` | integer | Number of deduplicated anomalies with severity `"medium"`. |
| `low` | integer | Number of deduplicated anomalies with severity `"low"`. |

---

## Example anomaly entry

```json
{
  "date": "2020-04-01",
  "value": 14.8,
  "type": "zscore",
  "score": 4.728,
  "severity": "high",
  "description": "Z-score 4.73 — high deviation from mean"
}
```

---

## Notes

- The `anomalies` array is sorted by `date` ascending.
- `score` semantics differ by `type` and should not be compared across detector types.
- The `history` arrays are parallel: `dates[i]` and `values[i]` correspond to the same observation.
- The root-level `anomaly_data.json` is consumed directly by `index.html` via a relative `fetch()` call. The identical file is also saved to `data/artifacts/anomaly_data.json` as an archival copy.
