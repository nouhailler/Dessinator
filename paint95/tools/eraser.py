"""
Eraser tool — paints with the background colour.
"""
from PyQt6.QtGui import QImage, QPainter, QBrush, QColor
from PyQt6.QtCore import QPoint, QRect, Qt
from .base import BaseTool

SIZES = [8, 16, 32]


class EraserTool(BaseTool):
    name = "eraser"

    def __init__(self) -> None:
        super().__init__()
        self.size: int = 16

    def _erase(self, image: QImage, pos: QPoint) -> None:
        p = QPainter(image)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self.background))
        half = self.size // 2
        p.drawRect(QRect(pos.x() - half, pos.y() - half, self.size, self.size))
        p.end()

    def _erase_line(self, image: QImage, p0: QPoint, p1: QPoint) -> None:
        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            t = i / steps
            x = round(p0.x() + dx * t)
            y = round(p0.y() + dy * t)
            self._erase(image, QPoint(x, y))

    def on_press(self, image, pos, button):
        self._erase(image, pos)
        self._last_point = pos
        return True

    def on_move(self, image, pos, button):
        if self._last_point is None:
            return False
        self._erase_line(image, self._last_point, pos)
        self._last_point = pos
        return True

    def on_release(self, image, pos, button):
        self._last_point = None
        return False
