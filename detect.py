"""
Economic Anomaly Detection Monitor
===================================
Ingests two FRED macroeconomic series (unemployment rate + CPI) and runs three
independent anomaly detection algorithms to flag statistically significant
deviations. Outputs anomaly_data.json consumed by the dashboard.

Data:  Federal Reserve Bank of St. Louis (FRED)
       UNRATE  — U.S. Unemployment Rate (seasonally adjusted, %)
       CPIAUCSL — Consumer Price Index, All Items (seasonally adjusted)

Usage:
    pip install pandas numpy scipy
    python detect.py
"""

import io
import json
import urllib.request
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"

SERIES = [
    {
        "id": "UNRATE",
        "name": "U.S. Unemployment Rate",
        "units": "Percent (Seasonally Adjusted)",
        "color": "#E8A020",
        "start": "2000-01-01",
    },
    {
        "id": "CPIAUCSL",
        "name": "Consumer Price Index",
        "units": "Index 1982-84=100 (Seasonally Adjusted)",
        "color": "#60a5fa",
        "start": "2000-01-01",
    },
]

OUTPUT_PATH = "anomaly_data.json"


def fetch_series(series_id: str, start: str) -> pd.Series:
    url = FRED_BASE.format(series_id)
    with urllib.request.urlopen(url) as resp:
        raw = resp.read().decode()
    df = pd.read_csv(io.StringIO(raw), parse_dates=["observation_date"])
    df.columns = ["date", "value"]
    df = df.set_index("date").sort_index()
    series = df["value"].replace(".", np.nan).astype(float).dropna()
    return series[start:]


def detect_zscore(series: pd.Series, threshold: float = 2.5) -> list[dict]:
    z = np.abs(stats.zscore(series.values))
    anomalies = []
    for i, (date, val) in enumerate(series.items()):
        if z[i] > threshold:
            severity = "high" if z[i] > 3.5 else "medium" if z[i] > 3.0 else "low"
            anomalies.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(float(val), 4),
                "type": "zscore",
                "score": round(float(z[i]), 3),
                "severity": severity,
                "description": f"Z-score {z[i]:.2f} — {severity} deviation from mean",
            })
    return anomalies


def detect_iqr(series: pd.Series, multiplier: float = 2.0) -> list[dict]:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
    anomalies = []
    for date, val in series.items():
        if val < lower or val > upper:
            dist = max(abs(val - lower), abs(val - upper)) / iqr
            severity = "high" if dist > 3.0 else "medium" if dist > 1.5 else "low"
            direction = "below" if val < lower else "above"
            anomalies.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(float(val), 4),
                "type": "iqr",
                "score": round(float(dist), 3),
                "severity": severity,
                "description": f"IQR outlier — {direction} expected range [{lower:.2f}, {upper:.2f}]",
            })
    return anomalies


def detect_cusum(series: pd.Series, threshold_sigma: float = 4.0) -> list[dict]:
    # Operate on month-over-month changes to avoid flagging natural trends
    diff = series.diff().dropna()
    mu = diff.mean()
    sigma = diff.std()
    if sigma == 0:
        return []

    k = 0.5 * sigma
    threshold = threshold_sigma * sigma
    cusum_pos, cusum_neg = 0.0, 0.0
    anomalies = []
    alarm_active = False

    # Map diff index back to original series dates
    for date, dv in diff.items():
        cusum_pos = max(0.0, cusum_pos + dv - mu - k)
        cusum_neg = max(0.0, cusum_neg - dv + mu - k)

        if (cusum_pos > threshold or cusum_neg > threshold) and not alarm_active:
            score = max(cusum_pos, cusum_neg) / sigma
            severity = "high" if score > 7 else "medium" if score > 5 else "low"
            direction = "upward" if cusum_pos > cusum_neg else "downward"
            anomalies.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(float(series[date]), 4),
                "type": "cusum",
                "score": round(float(score), 3),
                "severity": severity,
                "description": f"CUSUM {direction} regime shift (score {score:.1f}sigma)",
            })
            alarm_active = True
            cusum_pos, cusum_neg = 0.0, 0.0
        elif cusum_pos <= threshold and cusum_neg <= threshold:
            alarm_active = False

    return anomalies


def deduplicate_anomalies(anomalies: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    priority = {"high": 3, "medium": 2, "low": 1}
    for a in anomalies:
        key = a["date"]
        if key not in seen or priority[a["severity"]] > priority[seen[key]["severity"]]:
            seen[key] = a
    return sorted(seen.values(), key=lambda x: x["date"])


def process_series(meta: dict) -> dict:
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
            "period": f"{series.index[0].strftime('%b %Y')} – {series.index[-1].strftime('%b %Y')}",
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


def main():
    print("Economic Anomaly Detection Monitor")
    print("=" * 38)

    results = []
    for meta in SERIES:
        print(f"\nProcessing {meta['name']}...")
        data = process_series(meta)
        results.append(data)
        c = data["counts"]
        print(f"  Anomalies: {c['total_unique']} unique "
              f"({c['high']} high / {c['medium']} medium / {c['low']} low)")
        print(f"  Algorithms: Z-score={c['zscore']}, IQR={c['iqr']}, CUSUM={c['cusum']}")

    output = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "series": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
