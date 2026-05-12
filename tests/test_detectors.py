"""
tests/test_detectors.py
=======================
Unit tests for the three anomaly detection algorithms.

Each test constructs a synthetic time series with a known anomaly and verifies
that the corresponding detector flags the correct date.
"""

import numpy as np
import pandas as pd
import pytest

from src.detectors.zscore import detect_zscore
from src.detectors.iqr import detect_iqr
from src.detectors.cusum import detect_cusum


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_series(n: int = 50, seed: int = 42) -> pd.Series:
    """Return a date-indexed series of near-zero Gaussian noise."""
    rng = np.random.default_rng(seed)
    values = rng.normal(loc=0.0, scale=1.0, size=n)
    dates = pd.date_range("2000-01-01", periods=n, freq="MS")
    return pd.Series(values, index=dates, name="test")


# ---------------------------------------------------------------------------
# Z-score tests
# ---------------------------------------------------------------------------

class TestZScore:
    def test_zscore_detects_obvious_spike(self):
        """A value 10 sigma above the mean must be flagged by detect_zscore."""
        series = _make_series(n=50)
        # Inject a massive spike at index 10
        spike_date = series.index[10]
        series.iloc[10] = series.mean() + 10 * series.std()

        anomalies = detect_zscore(series, threshold=2.5)
        flagged_dates = {a["date"] for a in anomalies}

        assert spike_date.strftime("%Y-%m-%d") in flagged_dates, (
            "detect_zscore did not flag the injected spike"
        )

    def test_zscore_type_field(self):
        """All returned anomalies must carry type='zscore'."""
        series = _make_series(n=50)
        series.iloc[10] = series.mean() + 10 * series.std()

        anomalies = detect_zscore(series)
        assert all(a["type"] == "zscore" for a in anomalies)

    def test_zscore_high_severity(self):
        """A z-score above 3.5 must be classified as 'high' severity."""
        series = _make_series(n=50)
        series.iloc[10] = series.mean() + 10 * series.std()

        anomalies = detect_zscore(series)
        spike_anomaly = next(
            a for a in anomalies
            if a["date"] == series.index[10].strftime("%Y-%m-%d")
        )
        assert spike_anomaly["severity"] == "high"

    def test_zscore_clean_series_no_flags(self):
        """A perfectly uniform series should produce no anomalies."""
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        series = pd.Series([5.0] * 50, index=dates)

        anomalies = detect_zscore(series, threshold=2.5)
        assert anomalies == [], "Uniform series should not produce anomalies"

    def test_zscore_score_matches_threshold(self):
        """No returned anomaly should have score <= threshold."""
        series = _make_series(n=100, seed=0)
        series.iloc[20] = series.mean() + 5 * series.std()

        threshold = 2.5
        anomalies = detect_zscore(series, threshold=threshold)
        assert all(a["score"] > threshold for a in anomalies)


# ---------------------------------------------------------------------------
# IQR tests
# ---------------------------------------------------------------------------

class TestIQR:
    def test_iqr_detects_outlier_above_upper_fence(self):
        """A value well above Q3+2*IQR must be flagged."""
        # Use a narrow distribution; inject extreme outlier
        dates = pd.date_range("2000-01-01", periods=60, freq="MS")
        values = [5.0] * 60
        series = pd.Series(values, index=dates, dtype=float)
        # Tiny variance so IQR ≈ 0; use a range series instead
        series = pd.Series(
            [float(i) for i in range(60)], index=dates
        )
        # Insert a value far above Q3+2*IQR
        outlier_date = dates[30]
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        series.iloc[30] = q3 + 5 * iqr  # clearly above upper fence of 2*IQR

        anomalies = detect_iqr(series, multiplier=2.0)
        flagged_dates = {a["date"] for a in anomalies}

        assert outlier_date.strftime("%Y-%m-%d") in flagged_dates

    def test_iqr_skewed_series_outlier(self):
        """Create a right-skewed series with one extreme high value; verify flagged."""
        rng = np.random.default_rng(7)
        # Gamma distribution: right-skewed, positive
        values = list(rng.gamma(shape=2.0, scale=1.0, size=80))
        dates = pd.date_range("2000-01-01", periods=80, freq="MS")
        series = pd.Series(values, index=dates)

        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        # Inject a value at 4× IQR above Q3
        outlier_date = dates[40]
        series.iloc[40] = q3 + 4 * iqr

        anomalies = detect_iqr(series, multiplier=2.0)
        flagged_dates = {a["date"] for a in anomalies}

        assert outlier_date.strftime("%Y-%m-%d") in flagged_dates

    def test_iqr_type_field(self):
        """All returned anomalies must carry type='iqr'."""
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        values = list(range(50))
        series = pd.Series([float(v) for v in values], index=dates)
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        series.iloc[49] = q3 + 3 * (q3 - q1)

        anomalies = detect_iqr(series)
        assert all(a["type"] == "iqr" for a in anomalies)

    def test_iqr_direction_label_above(self):
        """Outlier above upper fence must include 'above' in description."""
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        series = pd.Series([5.0] * 50, index=dates, dtype=float)
        # Series with some spread
        for i in range(50):
            series.iloc[i] = float(i)
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        series.iloc[49] = q3 + 3 * (q3 - q1)

        anomalies = detect_iqr(series)
        high_date = dates[49].strftime("%Y-%m-%d")
        match = next((a for a in anomalies if a["date"] == high_date), None)
        assert match is not None
        assert "above" in match["description"]


# ---------------------------------------------------------------------------
# CUSUM tests
# ---------------------------------------------------------------------------

class TestCUSUM:
    def test_cusum_detects_level_shift(self):
        """A sudden upward level shift at index 15 must trigger a CUSUM alarm."""
        rng = np.random.default_rng(99)
        # Low-noise series with a clear step change at index 15
        values = list(rng.normal(0.0, 0.1, 15)) + list(rng.normal(3.0, 0.1, 35))
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        series = pd.Series(values, index=dates)

        anomalies = detect_cusum(series, threshold_sigma=4.0)

        assert len(anomalies) >= 1, "CUSUM did not detect the regime shift"

        # The alarm should fire at or near the shift point (index 15)
        alarm_date = pd.Timestamp(anomalies[0]["date"])
        shift_date = dates[15]
        delta_months = abs((alarm_date.year - shift_date.year) * 12
                           + alarm_date.month - shift_date.month)
        assert delta_months <= 5, (
            f"CUSUM alarm at {alarm_date} is too far from shift at {shift_date}"
        )

    def test_cusum_type_field(self):
        """All returned anomalies must carry type='cusum'."""
        rng = np.random.default_rng(42)
        values = list(rng.normal(0.0, 0.1, 10)) + list(rng.normal(5.0, 0.1, 40))
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        series = pd.Series(values, index=dates)

        anomalies = detect_cusum(series)
        assert all(a["type"] == "cusum" for a in anomalies)

    def test_cusum_direction_upward(self):
        """An upward level shift must produce a description containing 'upward'."""
        rng = np.random.default_rng(11)
        values = list(rng.normal(0.0, 0.1, 15)) + list(rng.normal(4.0, 0.1, 35))
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        series = pd.Series(values, index=dates)

        anomalies = detect_cusum(series, threshold_sigma=4.0)
        assert len(anomalies) >= 1
        assert "upward" in anomalies[0]["description"]

    def test_cusum_no_alarm_on_flat_series(self):
        """A flat constant series should produce no CUSUM alarms."""
        dates = pd.date_range("2000-01-01", periods=50, freq="MS")
        series = pd.Series([5.0] * 50, index=dates)

        anomalies = detect_cusum(series)
        assert anomalies == [], "Flat series should not trigger CUSUM alarm"

    def test_cusum_sigma_zero_returns_empty(self):
        """If sigma of differences is zero, detect_cusum must return []."""
        dates = pd.date_range("2000-01-01", periods=20, freq="MS")
        series = pd.Series([3.0] * 20, index=dates)

        result = detect_cusum(series)
        assert result == []
