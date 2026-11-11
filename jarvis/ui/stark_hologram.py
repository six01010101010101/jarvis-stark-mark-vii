"""Widget em Canvas vetorial da Máscara do Homem de Ferro em Holograma Azul Stark."""

from __future__ import annotations

import tkinter as tk


class StarkHologramMask(tk.Canvas):
    """Renderiza a máscara do Homem de Ferro em linhas vetoriais holográficas neon azul."""

    def __init__(self, parent: tk.Widget, size: int = 56, bg: str = "#020710", **kwargs) -> None:
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)
        self._size = size
        self._glow_color = "#00F0FF"
        self._dim_color = "#005577"
        self._eye_color = "#E0FFFF"
        self.draw_mask()

    def set_palette(self, glow: str = "#00F0FF", dim: str = "#005577", eye: str = "#E0FFFF", bg: str = "#020710") -> None:
        """Atualiza as cores do holograma de acordo com o tema claro/escuro."""
        self._glow_color = glow
        self._dim_color = dim
        self._eye_color = eye
        self.configure(bg=bg)
        self.draw_mask()

    def draw_mask(self) -> None:
        """Traça as coordenadas vetoriais proporcionais do capacete Mark VII."""
        self.delete("all")
        s = self._size
        # Escala unitária (0 a 100) convertida para o tamanho do canvas
        def p(x: float, y: float) -> tuple[float, float]:
            return (x * s / 100.0, y * s / 100.0)

        # 1. Cúpula e contorno externo do capacete (Helmet Shell)
        outer_points = [
            p(30, 8), p(50, 5), p(70, 8), p(85, 25), p(85, 55),
            p(78, 78), p(65, 92), p(50, 95), p(35, 92), p(22, 78),
            p(15, 55), p(15, 25),
        ]
        flattened_outer = [coord for pt in outer_points for coord in pt]
        self.create_polygon(flattened_outer, outline=self._glow_color, fill="", width=2, smooth=True)

        # 2. Placa frontal da face (Faceplate inner frame)
        faceplate_points = [
            p(28, 25), p(50, 22), p(72, 25), p(78, 48), p(68, 68),
            p(58, 74), p(42, 74), p(32, 68), p(22, 48),
        ]
        flattened_fp = [coord for pt in faceplate_points for coord in pt]
        self.create_polygon(flattened_fp, outline=self._dim_color, fill="", width=1)

        # 3. Olhos holográficos luminosos (Angular Slits)
        # Olho esquerdo
        eye_left = [p(30, 42), p(44, 45), p(43, 49), p(32, 47)]
        self.create_polygon([c for pt in eye_left for coord in pt for c in (coord,)], outline=self._glow_color, fill=self._eye_color, width=1)
        # Olho direito
        eye_right = [p(56, 45), p(70, 42), p(68, 47), p(57, 49)]
        self.create_polygon([c for pt in eye_right for coord in pt for c in (coord,)], outline=self._glow_color, fill=self._eye_color, width=1)

        # 4. Linhas de detalhamento da mandíbula e queixo
        self.create_line(*p(40, 78), *p(60, 78), fill=self._glow_color, width=1)
        self.create_line(*p(44, 85), *p(56, 85), fill=self._dim_color, width=1)
        self.create_line(*p(50, 10), *p(50, 22), fill=self._dim_color, width=1)
