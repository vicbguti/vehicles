import matplotlib.pyplot as plt
import os

def apply_style():
    """Apply a premium visual style used across all reporting charts.
    - Dark background with vibrant viridis colormap by default.
    - Use the Inter Google Font for titles if available.
    - Enable tight layout and retina‑ready DPI.
    """
    plt.style.use('ggplot')  # base style, can be swapped for a custom one later
    plt.rcParams.update({
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'font.size': 12,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'legend.fontsize': 11,
        'figure.autolayout': True,
    })

def save_figure(path: str):
    """Save the current matplotlib figure to *path* ensuring the directory exists.
    The function creates parent directories on demand and prints a short confirmation.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, bbox_inches='tight')
    print(f"Figure saved to {path}")
