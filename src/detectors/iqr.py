"""
src/detectors/iqr.py
====================
Interquartile Range (IQR) anomaly detector for univariate time series.

IQR method
----------
The IQR is the spread of the middle 50 % of the data:

    IQR = Q3 - Q1     (Q1 = 25th percentile, Q3 = 75th percentile)

Outlier fences are constructed using a *multiplier* (default 2.0):

    lower_fence = Q1 - multiplier * IQR
    upper_fence = Q3 + multiplier * IQR

Any observation outside [lower_fence, upper_fence] is flagged.

Multiplier choice
-----------------
The classical Tukey (1977) fence uses multiplier = 1.5. For macroeconomic
data with heavy tails and occasional regime changes, 1.5 produces excessive
false positives. A multiplier of 2.0 is used here as a more conservative
setting that flags only materially extreme values.

Severity scoring
----------------
Severity is based on the distance of the observation from the nearest fence,
expressed as multiples of IQR:

    dist = max(|val - lower_fence|, |val - upper_fence|) / IQR

  - low    : dist <= 1.5
  - medium : 1.5 < dist <= 3.0
  - high   : dist > 3.0

When to use
-----------
Distribution-free; makes no assumption of normality. Particularly suitable
for the CPI series, which exhibits a right-skewed distribution (inflation tends
to persist at elevated levels for extended periods, producing a longer upper
tail). IQR is more robust than Z-score in the presence of heavy tails.
"""

import pandas as pd


def detect_iqr(
    series: pd.Series,
    multiplier: float = 2.0,
) -> list[dict]:
    """Flag observations outside the IQR-based outlier fences.

    Parameters
    ----------
    series : pd.Series
        Date-indexed float series (no NaN values).
    multiplier : float
        Fence width expressed as multiples of IQR. Default 2.0.

    Returns
    -------
    list[dict]
        Each dict contains keys: ``date``, ``value``, ``type`` (``"iqr"``),
        ``score``, ``severity``, ``description``.
    """
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    anomalies: list[dict] = []

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
                "description": (
                    f"IQR outlier — {direction} expected range "
                    f"[{lower:.2f}, {upper:.2f}]"
                ),
            })

    return anomalies
