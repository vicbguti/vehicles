# -*- coding: utf-8 -*-
"""Configuration for trimming utilities.

DEFAULT_EXCLUDE defines column names that should not be considered metrics when
checking for all‑zero rows.  By default we exclude temporal helper columns that
are always non‑zero (e.g., ``year`` and ``month``).
"""

DEFAULT_EXCLUDE = ("year", "month")
