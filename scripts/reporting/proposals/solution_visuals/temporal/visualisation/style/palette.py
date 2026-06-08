"""Curated colour palette for vehicle classes.
The palette is deliberately high‑contrast to improve accessibility.
"""

# Primary colours –feel free to extend.
CANTON_CLASS_PALETTE = {
    "MOTOCICLETA": "#e63946",  # red
    "JEEP": "#1d3557",        # dark blue
    "AUTOMOVIL": "#457b9d",   # medium blue
    "CAMIONETA": "#ffb703",   # amber
    "CAMON": "#8d99ae",       # muted teal
    "CAMION": "#2a9d8f",
    "VOLQUETA": "#e9c46a",
    "ESPECIAL": "#f4a261",
    "TRAILER": "#6a994e",
    "TANQUERO": "#264653",
}

def get_palette():
    """Return a list of HEX colours preserving order of insertion.
    Useful for matplotlib colormaps.
    """
    return list(CANTON_CLASS_PALETTE.values())
