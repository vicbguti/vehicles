# -*- coding: utf-8 -*-
"""Package that aggregates styling helpers for visualisation plotters.

It re‑exports the public helpers so that existing imports
```
from .styling import _apply_style, _draw_aligned_labels, _render_annotation_table
```
continue to work while the implementation lives in dedicated modules.
"""

from .axis import _apply_style
from .label import _draw_aligned_labels
from .legend import _render_annotation_table

__all__ = ["_apply_style", "_draw_aligned_labels", "_render_annotation_table"]
