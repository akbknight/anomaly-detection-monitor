"""
src/detectors/zscore.py
=======================
Z-score anomaly detector for univariate time series.

Formula
-------
For each observation x_i in a series with mean mu and standard deviation sigma:

    z_i = |x_i - mu| / sigma

An observation is flagged when z_i > *threshold* (default 2.5).

Threshold interpretation
------------------------
Under a normal distribution:
  - z > 1.96 : ~5 % of observations (too noisy for anomaly detection)
  - z > 2.5  : ~1.2 % of observations  <-- default threshold
  - z > 3.0  : ~0.27 % of observations
  - z > 3.5  : ~0.046 % of observations (very rare; classified "high")

When to use
-----------
Best suited for series that are approximately stationary around a stable mean
(e.g., unemployment rate over a uniform economic regime). Less appropriate for
strongly trending series because the global mean and std are distorted by the
trend, inflating z-scores in the tails and suppressing them in the centre.

Severity buckets
----------------
  - low    : 2.5 < z <= 3.0
  - medium : 3.0 < z <= 3.5
  - high   : z > 3.5
"""

import numpy as np
import pandas as pd
from scipy import stats


def detect_zscore(
    series: pd.Series,
    threshold: float = 2.5,
) -> list[dict]:
    """Flag observations whose absolute Z-score exceeds *threshold*.

    Parameters
    ----------
    series : pd.Series
        Date-indexed float series (no NaN values).
    threshold : float
        Minimum absolute Z-score to trigger an anomaly flag. Default 2.5.

    Returns
    -------
    list[dict]
        Each dict contains keys: ``date``, ``value``, ``type`` (``"zscore"``),
        ``score``, ``severity``, ``description``.
    """
    z = np.abs(stats.zscore(series.values))
    anomalies: list[dict] = []

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
