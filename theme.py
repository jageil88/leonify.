"""Leonify Theme - zentrale Farben und Konstanten."""

# Haupt-Farben (electric lila/pink vibe)
BG = "#0a0a12"             # app-hintergrund, pitch dark
SURFACE = "#15111f"        # karten, leicht heller
SURFACE_ALT = "#1f1830"    # hover/selected
PRIMARY = "#A855F7"        # electric purple - haupt-accent
SECONDARY = "#EC4899"      # hot pink - secondary accent
TEXT = "#ffffff"           # primary text
TEXT_MUTED = "#9b8ea8"     # secondary text
TEXT_DIM = "#5a4e6e"       # tertiary text
BORDER = "#2a2040"         # subtile trennlinien
DANGER = "#ef4444"         # löschen, warnings

# Hex -> rgba float (0-1) für Kivy
def rgba(hex_color: str, alpha: float = 1.0):
    h = hex_color.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (r, g, b, alpha)

# vorkomputierte rgba-tuples
BG_RGBA = rgba(BG)
SURFACE_RGBA = rgba(SURFACE)
SURFACE_ALT_RGBA = rgba(SURFACE_ALT)
PRIMARY_RGBA = rgba(PRIMARY)
SECONDARY_RGBA = rgba(SECONDARY)
TEXT_RGBA = rgba(TEXT)
TEXT_MUTED_RGBA = rgba(TEXT_MUTED)
TEXT_DIM_RGBA = rgba(TEXT_DIM)
BORDER_RGBA = rgba(BORDER)
DANGER_RGBA = rgba(DANGER)
