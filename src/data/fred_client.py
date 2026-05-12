"""
src/data/fred_client.py
=======================
Client for fetching macroeconomic time series from the Federal Reserve Bank of
St. Louis (FRED) public CSV API.

API URL pattern:
    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>

No API key is required. FRED serves public CSV exports directly. The response
is a two-column CSV with columns ``observation_date`` and ``<SERIES_ID>``.
Missing observations are represented as the string ``"."`` and are dropped
before returning.
"""

import io
import time
import urllib.request
import urllib.error

import numpy as np
import pandas as pd

FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"

_MAX_RETRIES = 3
_BACKOFF_SECONDS = 1.0


def fetch_series(series_id: str, start: str) -> pd.Series:
    """Fetch a FRED data series and return observations from *start* onward.

    Downloads the full history of *series_id* from the FRED public CSV
    endpoint, parses dates, drops missing values (encoded as ``"."``), and
    slices to ``[start:]``.

    Retry logic: up to 3 attempts with 1-second linear backoff on any
    ``urllib`` error. If all attempts fail the final exception is re-raised.

    Parameters
    ----------
    series_id : str
        FRED series identifier, e.g. ``"UNRATE"`` or ``"CPIAUCSL"``.
    start : str
        ISO date string ``"YYYY-MM-DD"`` — data before this date is dropped.

    Returns
    -------
    pd.Series
        Date-indexed float series, index type ``DatetimeIndex``, sorted
        ascending. Index name is ``"date"``, series name is *series_id*.

    Examples
    --------
    >>> s = fetch_series("UNRATE", "2000-01-01")
    >>> s.index[0]
    Timestamp('2000-01-01 00:00:00')
    """
    url = FRED_BASE.format(series_id)
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            with urllib.request.urlopen(url) as resp:
                raw = resp.read().decode()
            break
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_BACKOFF_SECONDS)
    else:
        raise last_exc  # type: ignore[misc]

    df = pd.read_csv(io.StringIO(raw), parse_dates=["observation_date"])
    df.columns = ["date", "value"]
    df = df.set_index("date").sort_index()
    series = df["value"].replace(".", np.nan).astype(float).dropna()
    series.name = series_id
    return series[start:]
