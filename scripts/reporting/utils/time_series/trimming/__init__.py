# -*- coding: utf-8 -*-
"""Package initializer for the trimming utilities.

Re‑exports the public helper ``trim_zero_tail`` and the default exclusion list.
"""

from .core import trim_zero_tail
from .config import DEFAULT_EXCLUDE

__all__ = ["trim_zero_tail", "DEFAULT_EXCLUDE"]
