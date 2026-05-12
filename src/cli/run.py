"""
src/cli/run.py
==============
Command-line entry point for the Economic Anomaly Detection Monitor.

Invocation:
    python detect.py          (via root shim)
    detect-anomalies          (via pyproject.toml console_scripts)
    python -m src.cli.run     (direct module run)

Workflow:
    1. Iterate over each series defined in SERIES.
    2. Call process_series() to fetch data and run all three detectors.
    3. Assemble the full output dict with a generation timestamp.
    4. Write anomaly_data.json to root (for dashboard) and data/artifacts/.
"""

import pandas as pd

from src.pipeline.runner import process_series, write_output

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


def main() -> None:
    """Fetch FRED data, run anomaly detection, and write output JSON."""
    print("Economic Anomaly Detection Monitor")
    print("=" * 38)

    results = []
    for meta in SERIES:
        print(f"\nProcessing {meta['name']}...")
        data = process_series(meta)
        results.append(data)
        c = data["counts"]
        print(
            f"  Anomalies: {c['total_unique']} unique "
            f"({c['high']} high / {c['medium']} medium / {c['low']} low)"
        )
        print(
            f"  Algorithms: Z-score={c['zscore']}, "
            f"IQR={c['iqr']}, CUSUM={c['cusum']}"
        )

    output = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "series": results,
    }

    print()
    write_output(output)
    print("\nDone.")


if __name__ == "__main__":
    main()
