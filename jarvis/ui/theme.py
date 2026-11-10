"""Tokens visuais e geometria 3D holográfica Tony Stark (Arc Reactor & Iron Man Helmet Mark VII)."""

WINDOW_TITLE = "J.A.R.V.I.S. // STARK INDUSTRIES MARK VII"
WINDOW_GEOMETRY = "420x740"
INITIAL_TEXT = "MARK VII // SISTEMAS DEFENSIVOS E IA ONLINE"
LABEL_WRAP = 370

# Paleta Holográfica Stark Mark VII HUD
BG_COLOR = "#060A12"
CARD_BG = "#070B12"
FG_COLOR = "#00F0FF"
ACCENT_COLOR = "#FFB703"
ACCENT_CYAN = "#00F0FF"
ALERT_GREEN = "#00FF88"
MUTED_COLOR = "#16344E"
HOLO_CYAN = "#00F0FF"
HOLO_GREEN = "#00FF88"
HOLO_CORE = "#0077B6"
ACTIVE_BTN_BG = "#003B5C"
INACTIVE_BTN_BG = "#091726"

CANVAS_SIZE = 220
ANIMATION_INTERVAL_MS = 35

# Vértices 3D normalizados do Capacete e Núcleo do Homem de Ferro
IRONMAN_3D_VERTICES = (
    # Topo do crânio
    (0, -65, 0), (-25, -55, 15), (25, -55, 15), (-35, -40, 20), (35, -40, 20),
    # Linha da testa e sobrancelhas
    (-28, -20, 35), (28, -20, 35), (0, -22, 38),
    # Olho esquerdo
    (-26, -10, 36), (-10, -10, 37), (-24, -5, 36), (-12, -5, 37),
    # Olho direito
    (10, -10, 37), (26, -10, 36), (12, -5, 37), (24, -5, 36),
    # Placa facial e bochechas
    (-35, 10, 25), (35, 10, 25), (-20, 35, 30), (20, 35, 30),
    # Queixo
    (-10, 55, 25), (10, 55, 25), (0, 60, 25),
    # Lateral e têmporas
    (-45, -15, 0), (45, -15, 0), (-40, 20, -5), (40, 20, -5),
)

# Arestas de conexão para renderização wireframe do holograma 3D
IRONMAN_3D_EDGES = (
    # Contorno superior
    (0, 1), (0, 2), (1, 3), (2, 4), (1, 5), (2, 6), (5, 7), (6, 7),
    # Olho esquerdo
    (8, 9), (9, 11), (11, 10), (10, 8),
    # Olho direito
    (12, 13), (13, 15), (15, 14), (14, 12),
    # Máscara facial e queixo
    (5, 8), (6, 13), (8, 16), (13, 17), (16, 18), (17, 19),
    (18, 20), (19, 21), (20, 22), (21, 22),
    # Laterais da armadura
    (3, 23), (4, 24), (23, 25), (24, 26), (25, 18), (26, 19),
)
