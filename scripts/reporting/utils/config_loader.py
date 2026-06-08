import os
import yaml
import pandas as pd

def load_config():
    """Load the central configuration and resolve the project root.
    Returns a tuple (config_dict, project_root_path).
    Handles both possible relative locations of config.yaml.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    if not os.path.exists(config_path):
        # fallback used by existing scripts
        config_path = os.path.join(os.path.dirname(__file__), '../../../../../config/config.yaml')
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    return cfg, project_root
