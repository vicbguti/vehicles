# -*- coding: utf-8 -*-
"""Compatibility shim for the old trimming module.

The original implementation lived directly in this file.  After the refactor
the canonical implementation lives in ``utils.time_series.trimming.core``.
This shim re‑exports the function so that existing imports continue to work
without modification.
"""

from .core import trim_zero_tail

__all__ = ["trim_zero_tail"]
