"""Rectangular selection tool."""
from __future__ import annotations
from PyQt6.QtCore import QRect
from .base_tool import BaseTool


class SelectionTool(BaseTool):
    name = "Sélection"

    def __init__(self) -> None:
        super().__init__()
        self._x0 = 0
        self._y0 = 0
        self._active = False

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._x0 = x
        self._y0 = y
        self._active = True
        canvas.set_selection(None)
        return True

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        rect = QRect(
            min(self._x0, x), min(self._y0, y),
            abs(x - self._x0), abs(y - self._y0)
        )
        canvas.set_selection(rect)
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        self._active = False
        rect = QRect(
            min(self._x0, x), min(self._y0, y),
            abs(x - self._x0), abs(y - self._y0)
        )
        if rect.width() > 0 and rect.height() > 0:
            canvas.set_selection(rect)
        else:
            canvas.set_selection(None)
        return True
