"""
Brush tool — configurable size, round or square shape.
"""
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import QPoint, QRect, Qt
from .base import BaseTool

SIZES = [1, 3, 5, 8]


class BrushTool(BaseTool):
    name = "brush"

    def __init__(self) -> None:
        super().__init__()
        self.size: int = 3
        self.round_shape: bool = True

    def _paint(self, image: QImage, pos: QPoint, color: QColor) -> None:
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        half = self.size // 2
        rect = QRect(pos.x() - half, pos.y() - half, self.size, self.size)
        if self.round_shape:
            p.drawEllipse(rect)
        else:
            p.drawRect(rect)
        p.end()

    def _paint_line(self, image: QImage, p0: QPoint, p1: QPoint, color: QColor) -> None:
        """Draw brush stamps along a line between two points."""
        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            t = i / steps
            x = round(p0.x() + dx * t)
            y = round(p0.y() + dy * t)
            self._paint(image, QPoint(x, y), color)

    def on_press(self, image, pos, button):
        color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
        self._active_color = color
        self._paint(image, pos, color)
        self._last_point = pos
        return True

    def on_move(self, image, pos, button):
        if self._last_point is None:
            return False
        self._paint_line(image, self._last_point, pos, self._active_color)
        self._last_point = pos
        return True

    def on_release(self, image, pos, button):
        self._last_point = None
        return False
