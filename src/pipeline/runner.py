"""
src/pipeline/runner.py
======================
Orchestration layer: runs all three detectors on a single FRED series,
deduplicates by date, and returns a structured result dictionary.

The output dict schema matches the anomaly_data.json format consumed by
index.html. Two copies of the output are written:
  - anomaly_data.json         (root) — required by the index.html dashboard
  - data/artifacts/anomaly_data.json — archival copy
"""

import os

from src.data.fred_client import fetch_series
from src.detectors import detect_zscore, detect_iqr, detect_cusum

# Root output path — must match what index.html fetches
OUTPUT_PATH = "anomaly_data.json"
ARTIFACTS_PATH = "data/artifacts/anomaly_data.json"


def deduplicate_anomalies(anomalies: list[dict]) -> list[dict]:
    """Collapse multiple detections on the same date to the highest-severity one.

    When Z-score, IQR, and CUSUM all flag the same month, retaining three
    separate entries would over-count the event. This function keeps only the
    detection with the highest severity for each calendar date, then returns
    results sorted chronologically.

    Parameters
    ----------
    anomalies : list[dict]
        Combined list of anomaly dicts from all detectors. Each dict must
        contain at least ``"date"`` and ``"severity"`` keys.

    Returns
    -------
    list[dict]
        Deduplicated list sorted by ``"date"`` ascending.
    """
    seen: dict[str, dict] = {}
    priority = {"high": 3, "medium": 2, "low": 1}

    for a in anomalies:
        key = a["date"]
        if key not in seen or priority[a["severity"]] > priority[seen[key]["severity"]]:
            seen[key] = a

    return sorted(seen.values(), key=lambda x: x["date"])


def process_series(meta: dict) -> dict:
    """Fetch one FRED series, run all detectors, and return a result dict.

    Parameters
    ----------
    meta : dict
        Series metadata with keys: ``id``, ``name``, ``units``, ``color``,
        ``start`` (ISO date string).

    Returns
    -------
    dict
        Contains sub-dicts ``meta``, ``history``, ``anomalies``, ``counts``.
        This structure is directly serialised into anomaly_data.json.
    """
    print(f"  Fetching {meta['id']}...")
    series = fetch_series(meta["id"], meta["start"])

    print(f"  Running anomaly detection ({len(series)} months)...")
    z_anomalies = detect_zscore(series)
    iqr_anomalies = detect_iqr(series)
    cusum_anomalies = detect_cusum(series)

    all_anomalies = z_anomalies + iqr_anomalies + cusum_anomalies
    deduped = deduplicate_anomalies(all_anomalies)

    counts = {
        "zscore": len(z_anomalies),
        "iqr": len(iqr_anomalies),
        "cusum": len(cusum_anomalies),
        "total_unique": len(deduped),
        "high": sum(1 for a in deduped if a["severity"] == "high"),
        "medium": sum(1 for a in deduped if a["severity"] == "medium"),
        "low": sum(1 for a in deduped if a["severity"] == "low"),
    }

    return {
        "meta": {
            "id": meta["id"],
            "name": meta["name"],
            "units": meta["units"],
            "color": meta["color"],
            "source": "Federal Reserve Bank of St. Louis (FRED)",
            "source_url": f"https://fred.stlouisfed.org/series/{meta['id']}",
            "period": (
                f"{series.index[0].strftime('%b %Y')} – "
                f"{series.index[-1].strftime('%b %Y')}"
            ),
            "n_months": len(series),
            "latest_value": round(float(series.iloc[-1]), 4),
            "latest_date": series.index[-1].strftime("%B %Y"),
            "mean": round(float(series.mean()), 4),
            "std": round(float(series.std()), 4),
        },
        "history": {
            "dates": [d.strftime("%Y-%m-%d") for d in series.index],
            "values": [round(float(v), 4) for v in series],
        },
        "anomalies": deduped,
        "counts": counts,
    }


def write_output(output: dict) -> None:
    """Write output dict to both root anomaly_data.json and data/artifacts/.

    Parameters
    ----------
    output : dict
        Fully assembled output object (with ``generated`` and ``series`` keys).
    """
    import json

    # Root copy — required for index.html dashboard
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved: {OUTPUT_PATH}")

    # Archival copy
    os.makedirs(os.path.dirname(ARTIFACTS_PATH), exist_ok=True)
    with open(ARTIFACTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved: {ARTIFACTS_PATH}")
