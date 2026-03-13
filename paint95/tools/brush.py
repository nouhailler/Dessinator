"""Brush tool — configurable size (round or square)."""
from __future__ import annotations
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtCore import Qt
from .base_tool import BaseTool

SIZES = [1, 3, 5, 8]
SHAPES = ["round", "square"]


class BrushTool(BaseTool):
    name = "Pinceau"

    def __init__(self) -> None:
        super().__init__()
        self.size: int = 3
        self.shape: str = "round"
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
        self._stamp(canvas.image, x, y, self._color(button))
        return True

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        color = self._color(button)
        steps = max(abs(x - self._last_x), abs(y - self._last_y), 1)
        for i in range(steps + 1):
            t = i / steps
            ix = int(self._last_x + t * (x - self._last_x))
            iy = int(self._last_y + t * (y - self._last_y))
            self._stamp(canvas.image, ix, iy, color)
        self._last_x = x
        self._last_y = y
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = False
        return False

    # ── helpers ─────────────────────────────────────────────────────────────
    def _color(self, button: int) -> QColor:
        return self._fg if button == 1 else self._bg

    def _stamp(self, image, cx: int, cy: int, color: QColor) -> None:
        r = max(self.size // 2, 0)
        painter = QPainter(image)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        if self.shape == "round":
            painter.drawEllipse(cx - r, cy - r, self.size, self.size)
        else:
            painter.fillRect(cx - r, cy - r, self.size, self.size, color)
        painter.end()
