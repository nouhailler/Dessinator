"""
Abstract base class for all drawing tools.
"""
from PyQt6.QtGui import QPainter, QColor, QImage
from PyQt6.QtCore import QObject, QPoint


class BaseTool(QObject):
    """
    Every tool receives press / move / release events and draws
    directly onto a QImage via a QPainter that the canvas provides.
    """

    name: str = "base"
    cursor: str = "crosshair"   # Qt cursor name or path

    def __init__(self) -> None:
        super().__init__()
        self.foreground: QColor = QColor("#000000")
        self.background: QColor = QColor("#FFFFFF")
        self._last_point: QPoint | None = None

    def set_colors(self, fg: QColor, bg: QColor) -> None:
        self.foreground = fg
        self.background = bg

    # ------------------------------------------------------------------
    # Override in subclasses
    # ------------------------------------------------------------------
    def on_press(self, image: QImage, pos: QPoint, button: int) -> bool:
        """Return True if the canvas should be repainted."""
        return False

    def on_move(self, image: QImage, pos: QPoint, button: int) -> bool:
        return False

    def on_release(self, image: QImage, pos: QPoint, button: int) -> bool:
        return False

    # overlay drawn *on top* of the canvas (not committed)
    def draw_overlay(self, painter: QPainter, pos: QPoint) -> None:
        pass
