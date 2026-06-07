# -*- coding: utf-8 -*-
"""Configuration loader for the temporal trends canton‑class workflow.
It expects a YAML file at ``scripts/config/config.yaml`` (relative to the
project root) but falls back to a minimal inline configuration if the file
is missing.
"""
import os
import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "data": {
        "base_dir": "data/raw",
        "files_pattern": "*.csv",
    },
    "output": {
        "top12": "reports/figures/proposals/temporal/temporal_trends_canton_class_top12.png",
        "by_province_dir": "reports/figures/proposals/temporal/by_province",
    },
}

def load_config(config_path: str | None = None) -> dict:
    """Load configuration from ``config_path``.

    Parameters
    ----------
    config_path: str | None
        Absolute or relative path to a YAML configuration file. If ``None``
        the function looks for ``scripts/config/config.yaml`` relative to the
        project root.

    Returns
    -------
    dict
        Configuration dictionary merged with ``DEFAULT_CONFIG``.
    """
    if config_path is None:
        # Resolve path relative to the repository root (assumed to be two levels up)
        project_root = Path(__file__).resolve().parents[4]
        config_path = project_root / "scripts" / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    if config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        # Simple shallow merge – user config overrides defaults
        cfg = {**DEFAULT_CONFIG, **user_cfg}
        return cfg
    else:
        # No config file – use defaults
        return DEFAULT_CONFIG

if __name__ == "__main__":
    print(load_config())
