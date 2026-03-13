"""Pencil tool — 1-pixel Bresenham line drawing."""
from __future__ import annotations
from PyQt6.QtGui import QColor
from .base_tool import BaseTool


class PencilTool(BaseTool):
    name = "Crayon"

    def __init__(self) -> None:
        super().__init__()
        self._last_x = -1
        self._last_y = -1
        self._active = False
        self._button = 1

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = True
        self._button = button
        self._last_x = x
        self._last_y = y
        canvas.save_undo()
        self._plot(canvas.image, x, y, self._color(button))
        return True

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        self._bresenham(canvas.image, self._last_x, self._last_y, x, y, self._color(button))
        self._last_x = x
        self._last_y = y
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = False
        return False

    # ── helpers ─────────────────────────────────────────────────────────────
    def _color(self, button: int) -> QColor:
        return self._fg if button == 1 else self._bg

    def _plot(self, image, x: int, y: int, color: QColor) -> None:
        if 0 <= x < image.width() and 0 <= y < image.height():
            image.setPixelColor(x, y, color)

    def _bresenham(self, image, x0: int, y0: int, x1: int, y1: int, color: QColor) -> None:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._plot(image, x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
