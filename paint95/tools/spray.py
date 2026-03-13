"""Spray / aerograph tool — random pixel distribution inside a circle."""
from __future__ import annotations
import math
import random
from PyQt6.QtGui import QColor
from .base_tool import BaseTool


class SprayTool(BaseTool):
    name = "Aérographe"

    def __init__(self) -> None:
        super().__init__()
        self.radius: int = 15
        self.density: int = 30
        self._active = False
        self._button = 1

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = True
        self._button = button
        canvas.save_undo()
        self._spray(canvas.image, x, y, self._color(button))
        return True

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        self._spray(canvas.image, x, y, self._color(button))
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = False
        return False

    def _color(self, button: int) -> QColor:
        return self._fg if button == 1 else self._bg

    def _spray(self, image, cx: int, cy: int, color: QColor) -> None:
        w, h = image.width(), image.height()
        for _ in range(self.density):
            angle = random.uniform(0.0, math.tau)
            dist = random.uniform(0.0, self.radius)
            px = int(cx + dist * math.cos(angle))
            py = int(cy + dist * math.sin(angle))
            if 0 <= px < w and 0 <= py < h:
                image.setPixelColor(px, py, color)
