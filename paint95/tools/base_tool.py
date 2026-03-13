"""Abstract base class for all drawing tools."""
from __future__ import annotations
from abc import ABC
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class BaseTool(ABC):
    name: str = "tool"
    cursor: Qt.CursorShape = Qt.CursorShape.CrossCursor

    def __init__(self) -> None:
        self._fg: QColor = QColor("#000000")
        self._bg: QColor = QColor("#ffffff")

    def set_colors(self, fg: QColor, bg: QColor) -> None:
        self._fg = fg
        self._bg = bg

    # ── event hooks (override as needed) ────────────────────────────────────
    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        """Called on mouse button press. Return True if canvas needs repaint."""
        return False

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        """Called on mouse move while button held. Return True if canvas needs repaint."""
        return False

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        """Called on mouse button release. Return True if canvas needs repaint."""
        return False

    def on_key_press(self, key: int) -> bool:
        return False
