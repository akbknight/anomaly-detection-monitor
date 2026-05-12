"""
tests/test_pipeline.py
======================
Unit tests for the pipeline orchestration layer, focusing on the
deduplicate_anomalies() function.
"""

import pytest

from src.pipeline.runner import deduplicate_anomalies


class TestDeduplicateAnomalies:
    def _make_anomaly(self, date: str, severity: str, atype: str = "zscore") -> dict:
        return {
            "date": date,
            "value": 5.0,
            "type": atype,
            "score": 3.0,
            "severity": severity,
            "description": f"Test anomaly — {severity}",
        }

    def test_same_date_keeps_higher_severity(self):
        """Two entries on the same date: only the higher severity should survive."""
        anomalies = [
            self._make_anomaly("2020-04-01", "low", "iqr"),
            self._make_anomaly("2020-04-01", "high", "zscore"),
        ]
        result = deduplicate_anomalies(anomalies)

        assert len(result) == 1
        assert result[0]["severity"] == "high"
        assert result[0]["type"] == "zscore"

    def test_same_date_medium_vs_low(self):
        """Medium beats low on the same date."""
        anomalies = [
            self._make_anomaly("2009-10-01", "low", "cusum"),
            self._make_anomaly("2009-10-01", "medium", "iqr"),
        ]
        result = deduplicate_anomalies(anomalies)

        assert len(result) == 1
        assert result[0]["severity"] == "medium"

    def test_different_dates_all_kept(self):
        """Entries on different dates must all be preserved."""
        anomalies = [
            self._make_anomaly("2008-11-01", "high"),
            self._make_anomaly("2020-04-01", "high"),
            self._make_anomaly("2021-06-01", "medium"),
        ]
        result = deduplicate_anomalies(anomalies)

        assert len(result) == 3

    def test_result_sorted_by_date(self):
        """Output must be sorted chronologically ascending."""
        anomalies = [
            self._make_anomaly("2021-06-01", "medium"),
            self._make_anomaly("2008-11-01", "high"),
            self._make_anomaly("2020-04-01", "high"),
        ]
        result = deduplicate_anomalies(anomalies)

        dates = [a["date"] for a in result]
        assert dates == sorted(dates), "deduplicate_anomalies output is not sorted"

    def test_empty_input_returns_empty(self):
        """Empty input must return an empty list."""
        assert deduplicate_anomalies([]) == []

    def test_single_entry_passthrough(self):
        """A single anomaly should pass through unchanged."""
        anomalies = [self._make_anomaly("2020-04-01", "high")]
        result = deduplicate_anomalies(anomalies)

        assert len(result) == 1
        assert result[0]["date"] == "2020-04-01"

    def test_three_algorithms_same_date(self):
        """When all three detectors flag the same date, only the highest survives."""
        anomalies = [
            self._make_anomaly("2020-04-01", "low", "iqr"),
            self._make_anomaly("2020-04-01", "medium", "cusum"),
            self._make_anomaly("2020-04-01", "high", "zscore"),
        ]
        result = deduplicate_anomalies(anomalies)

        assert len(result) == 1
        assert result[0]["severity"] == "high"
        assert result[0]["type"] == "zscore"

    def test_first_entry_wins_on_tie(self):
        """When two entries on the same date have identical severity, first one is kept."""
        anomalies = [
            self._make_anomaly("2020-04-01", "medium", "zscore"),
            self._make_anomaly("2020-04-01", "medium", "iqr"),
        ]
        result = deduplicate_anomalies(anomalies)

        assert len(result) == 1
        # First entry wins (no overwrite when equal priority)
        assert result[0]["type"] == "zscore"
