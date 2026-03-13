"""Pipette (colour picker) tool."""
from __future__ import annotations
from typing import Callable
from PyQt6.QtGui import QColor
from .base_tool import BaseTool


class PipetteTool(BaseTool):
    name = "Pipette"

    def __init__(self) -> None:
        super().__init__()
        self._on_fg: Callable[[QColor], None] | None = None
        self._on_bg: Callable[[QColor], None] | None = None

    def set_callbacks(self,
                      fg_cb: Callable[[QColor], None],
                      bg_cb: Callable[[QColor], None]) -> None:
        self._on_fg = fg_cb
        self._on_bg = bg_cb

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        img = canvas.image
        if 0 <= x < img.width() and 0 <= y < img.height():
            color = img.pixelColor(x, y)
            if button == 1 and self._on_fg:
                self._on_fg(color)
            elif button == 2 and self._on_bg:
                self._on_bg(color)
        return False
