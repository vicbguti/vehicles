import os
import sys
# Ensure utils package is on path (scripts/reporting)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../scripts/reporting')))

"""Common utilities for temporal visualisation scripts.
Provides convenient imports for date parsing and metric trimming.
"""

# Re‑export date parsing utilities from the project's utils package
from utils.date import parse_date, parse_slash_date

# Re‑export the metric trimming helper
from utils.time_series.trimming import trim_zero_tail

__all__ = ["parse_date", "parse_slash_date", "trim_zero_tail"]
