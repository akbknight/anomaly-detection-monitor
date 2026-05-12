"""
src/detectors/cusum.py
======================
CUSUM (Cumulative Sum) anomaly detector for univariate time series.

Algorithm — Page's CUSUM (1954)
--------------------------------
The CUSUM chart was introduced by E. S. Page (1954) as a sequential test for
detecting a shift in the mean of a process. It accumulates evidence of a
departure from an expected level across time, making it sensitive to *sustained*
directional changes that point-based methods (Z-score, IQR) would miss.

Two-sided CUSUM
~~~~~~~~~~~~~~~
Two accumulators are maintained simultaneously:

    S+_t = max(0,  S+_{t-1} + d_t - mu - k)   # upward shift detector
    S-_t = max(0,  S-_{t-1} - d_t + mu - k)   # downward shift detector

where:
  - d_t  = first difference of the series at time t  (x_t - x_{t-1})
  - mu   = mean of the differenced series
  - k    = slack parameter  (reference value) = 0.5 * sigma
  - sigma = standard deviation of the differenced series

An alarm fires when S+_t > h **or** S-_t > h, where h = threshold_sigma * sigma.

Operating on differences
~~~~~~~~~~~~~~~~~~~~~~~~
The raw series (e.g., the unemployment rate) has a natural level that shifts
across economic cycles. Applying CUSUM to raw levels would trigger alarms
continuously as the series drifts between regimes. By differencing first
(month-over-month changes), the input to CUSUM is approximately stationary with
a near-zero mean, so the chart only triggers when the *rate of change* itself
becomes abnormally persistent.

Slack parameter k = 0.5 * sigma
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The reference value k controls sensitivity. Setting k = 0.5 * sigma is the
standard recommendation from statistical process control literature
(Montgomery, 2012, "Introduction to Statistical Quality Control", 7th ed.).
It provides a reasonable balance between detection speed and false-alarm rate:
  - Too small k: very sensitive, many false alarms
  - Too large k: slow to detect real shifts

Threshold h = 4 * sigma
~~~~~~~~~~~~~~~~~~~~~~~~
h is calibrated to produce approximately 1 false alarm per 200 observations
at the expected noise level, consistent with ARL (Average Run Length) analysis
for a Gaussian process (Montgomery 2012, Table 9.2).

Alarm reset logic
~~~~~~~~~~~~~~~~~
On alarm, both S+ and S- are reset to zero. This prevents the chart from
"camping" on a past event and allows detection of subsequent shifts. The alarm
flag is cleared only when both accumulators fall back below the threshold, so
consecutive months within a single event are not double-counted.
"""

import pandas as pd


def detect_cusum(
    series: pd.Series,
    threshold_sigma: float = 4.0,
) -> list[dict]:
    """Detect sustained regime shifts using Page's two-sided CUSUM chart.

    Operates on month-over-month first differences of *series* to avoid
    flagging natural long-run trends as anomalies.

    Parameters
    ----------
    series : pd.Series
        Date-indexed float series (no NaN values).
    threshold_sigma : float
        Alarm threshold expressed as multiples of the standard deviation of
        first differences. Default 4.0 (h = 4σ).

    Returns
    -------
    list[dict]
        Each dict contains keys: ``date``, ``value``, ``type`` (``"cusum"``),
        ``score``, ``severity``, ``description``. One entry is emitted per
        distinct alarm event (the date of first threshold crossing).
    """
    # Operate on first differences to handle non-stationary levels
    diff = series.diff().dropna()
    mu = diff.mean()
    sigma = diff.std()

    if sigma == 0:
        return []

    k = 0.5 * sigma
    threshold = threshold_sigma * sigma
    cusum_pos, cusum_neg = 0.0, 0.0
    anomalies: list[dict] = []
    alarm_active = False

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
                "description": (
                    f"CUSUM {direction} regime shift (score {score:.1f}sigma)"
                ),
            })
            # Reset accumulators after alarm
            alarm_active = True
            cusum_pos, cusum_neg = 0.0, 0.0
        elif cusum_pos <= threshold and cusum_neg <= threshold:
            alarm_active = False

    return anomalies
