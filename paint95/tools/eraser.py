"""Eraser tool — paints background colour over a square area."""
from __future__ import annotations
from PyQt6.QtGui import QPainter
from .base_tool import BaseTool

SIZES = [8, 16, 32]


class EraserTool(BaseTool):
    name = "Gomme"

    def __init__(self) -> None:
        super().__init__()
        self.size: int = 16
        self._last_x = -1
        self._last_y = -1
        self._active = False

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = True
        self._last_x = x
        self._last_y = y
        canvas.save_undo()
        self._erase(canvas.image, x, y)
        return True

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        steps = max(abs(x - self._last_x), abs(y - self._last_y), 1)
        for i in range(steps + 1):
            t = i / steps
            self._erase(canvas.image,
                        int(self._last_x + t * (x - self._last_x)),
                        int(self._last_y + t * (y - self._last_y)))
        self._last_x = x
        self._last_y = y
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = False
        return False

    def _erase(self, image, cx: int, cy: int) -> None:
        r = self.size // 2
        painter = QPainter(image)
        painter.fillRect(cx - r, cy - r, self.size, self.size, self._bg)
        painter.end()
