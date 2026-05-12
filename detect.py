"""
detect.py — compatibility shim
================================
This file exists for backwards compatibility and convenience. It delegates
entirely to ``src.cli.run:main``, which is the canonical entry point for the
Economic Anomaly Detection Monitor.

Usage (unchanged from previous versions):
    python detect.py

Output (unchanged):
    anomaly_data.json — root copy for the index.html dashboard
    data/artifacts/anomaly_data.json — archival copy

For the full implementation see src/.
"""

from src.cli.run import main

if __name__ == "__main__":
    main()
