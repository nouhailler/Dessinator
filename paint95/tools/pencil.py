"""
Pencil tool — 1-pixel drawing using Bresenham's line algorithm.
"""
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import QPoint, Qt
from .base import BaseTool


def _bresenham(x0: int, y0: int, x1: int, y1: int):
    """Yield (x, y) integer coordinates along the line."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


class PencilTool(BaseTool):
    name = "pencil"

    def _draw_line(self, image: QImage, p0: QPoint, p1: QPoint, color: QColor) -> None:
        w, h = image.width(), image.height()
        rgb = color.rgb()
        for x, y in _bresenham(p0.x(), p0.y(), p1.x(), p1.y()):
            if 0 <= x < w and 0 <= y < h:
                image.setPixel(x, y, rgb)

    def on_press(self, image, pos, button):
        color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
        self._draw_line(image, pos, pos, color)
        self._last_point = pos
        self._active_color = color
        return True

    def on_move(self, image, pos, button):
        if self._last_point is None:
            return False
        self._draw_line(image, self._last_point, pos, self._active_color)
        self._last_point = pos
        return True

    def on_release(self, image, pos, button):
        self._last_point = None
        return False
