"""Tokens visuais, paletas Claro/Escuro e geometria holográfica Tony Stark."""

from __future__ import annotations

WINDOW_TITLE = "J.A.R.V.I.S. // STARK INDUSTRIES MARK VII"
WINDOW_GEOMETRY = "520x860"
INITIAL_TEXT = "MARK VII // SISTEMAS DEFENSIVOS E IA ONLINE"
LABEL_WRAP = 480

DARK_THEME: dict[str, str] = {
    "name": "dark",
    "bg": "#060A12",
    "card_bg": "#09111E",
    "fg": "#00F0FF",
    "text": "#E0F7FA",
    "accent": "#00F0FF",
    "dim": "#0E334D",
    "active_btn": "#005073",
    "inactive_btn": "#0C1826",
    "hologram_glow": "#00F0FF",
    "hologram_dim": "#005577",
    "hologram_eye": "#E0FFFF",
}

LIGHT_THEME: dict[str, str] = {
    "name": "light",
    "bg": "#EBF2F7",
    "card_bg": "#FFFFFF",
    "fg": "#005270",
    "text": "#102A43",
    "accent": "#007799",
    "dim": "#BAC7D5",
    "active_btn": "#BEE3F8",
    "inactive_btn": "#D9E2EC",
    "hologram_glow": "#007799",
    "hologram_dim": "#7AA5B8",
    "hologram_eye": "#004466",
}


def get_theme_palette(mode: str = "dark") -> dict[str, str]:
    """Retorna o dicionário de cores para o tema especificado ('dark' ou 'light')."""
    return LIGHT_THEME if mode.lower() == "light" else DARK_THEME


# Constantes de compatibilidade retroativa
BG_COLOR = DARK_THEME["bg"]
CARD_BG = DARK_THEME["card_bg"]
FG_COLOR = DARK_THEME["fg"]
ACCENT_COLOR = "#FFB703"
ACCENT_CYAN = DARK_THEME["accent"]
ALERT_GREEN = "#00FF88"
MUTED_COLOR = DARK_THEME["dim"]
HOLO_CYAN = DARK_THEME["fg"]
HOLO_GREEN = "#00FF88"
HOLO_CORE = "#0077B6"
ACTIVE_BTN_BG = DARK_THEME["active_btn"]
INACTIVE_BTN_BG = DARK_THEME["inactive_btn"]

CANVAS_SIZE = 180
ANIMATION_INTERVAL_MS = 35

IRONMAN_3D_VERTICES = (
    (0, -65, 0), (-25, -55, 15), (25, -55, 15), (-35, -40, 20), (35, -40, 20),
    (-28, -20, 35), (28, -20, 35), (0, -22, 38),
    (-26, -10, 36), (-10, -10, 37), (-24, -5, 36), (-12, -5, 37),
    (10, -10, 37), (26, -10, 36), (12, -5, 37), (24, -5, 36),
    (-35, 10, 25), (35, 10, 25), (-20, 35, 30), (20, 35, 30),
    (-10, 55, 25), (10, 55, 25), (0, 60, 25),
    (-45, -15, 0), (45, -15, 0), (-40, 20, -5), (40, 20, -5),
)

IRONMAN_3D_EDGES = (
    (0, 1), (0, 2), (1, 3), (2, 4), (1, 5), (2, 6), (5, 7), (6, 7),
    (8, 9), (9, 11), (11, 10), (10, 8),
    (12, 13), (13, 15), (15, 14), (14, 12),
    (5, 8), (6, 13), (8, 16), (13, 17), (16, 18), (17, 19),
    (18, 20), (19, 21), (20, 22), (21, 22),
    (3, 23), (4, 24), (23, 25), (24, 26), (25, 18), (26, 19),
)
