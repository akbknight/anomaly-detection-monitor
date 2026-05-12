"""Anomaly detection algorithms: Z-score, IQR, and CUSUM."""

from .zscore import detect_zscore
from .iqr import detect_iqr
from .cusum import detect_cusum

__all__ = ["detect_zscore", "detect_iqr", "detect_cusum"]
