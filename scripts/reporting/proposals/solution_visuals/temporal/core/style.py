def apply_style(ax, title: str, ylabel: str) -> None:
    """Apply a minimal consistent style to a matplotlib Axes.

    This helper sets the plot title and y‑axis label, removes the top and
    right spines for a cleaner look, and enables a grid with a light dash
    pattern. It mirrors the style expectations of the original project
    without pulling in any external theming libraries.
    """
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
