import pandas as pd

# Re-export the shared implementation from the core module
from .core import trim_zero_tail

# Default columns to exclude when trimming zero rows
from utils.time_series.trimming.config import DEFAULT_EXCLUDE

__all__ = ["trim_zero_tail", "DEFAULT_EXCLUDE"]
