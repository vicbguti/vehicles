# -*- coding: utf-8 -*-
"""Aggregator package exposing helper functions for temporal data.

This module re‑exports the most common aggregation helpers so callers can
import directly from ``temporal.core.aggregator``:

```python
from temporal.core.aggregator import (
    aggregate_overall,
    aggregate_by_class,
    aggregate_by_province,
    aggregate_combined,
    aggregate_province_df,
    aggregate_combined_df,
)
```
"""

from .overall import aggregate_overall
from .by_class import aggregate_by_class
from .by_province import aggregate_by_province
from .combined import aggregate_combined
from .by_canton import aggregate_by_canton

__all__ = [
    "aggregate_overall",
    "aggregate_by_class",
    "aggregate_by_province",
    "aggregate_combined",
    "aggregate_by_canton",
]

