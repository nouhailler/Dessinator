"""
Flood-fill tool — scanline flood fill algorithm.
"""
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import QPoint, Qt
from .base import BaseTool


def _scanline_fill(image: QImage, x: int, y: int, fill_color: QColor) -> None:
    """Scanline flood fill. Modifies image in-place."""
    w, h = image.width(), image.height()
    target_rgb = image.pixel(x, y)
    fill_rgb = fill_color.rgb()

    if target_rgb == fill_rgb:
        return

    stack: list[tuple[int, int]] = [(x, y)]
    visited: set[tuple[int, int]] = set()

    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        if cx < 0 or cx >= w or cy < 0 or cy >= h:
            continue
        if image.pixel(cx, cy) != target_rgb:
            continue

        # Scan left
        lx = cx
        while lx >= 0 and image.pixel(lx, cy) == target_rgb:
            lx -= 1
        lx += 1

        # Scan right
        rx = cx
        while rx < w and image.pixel(rx, cy) == target_rgb:
            rx += 1
        rx -= 1

        # Fill the span
        for nx in range(lx, rx + 1):
            image.setPixel(nx, cy, fill_rgb)
            visited.add((nx, cy))
            # Enqueue above and below
            if cy > 0 and image.pixel(nx, cy - 1) == target_rgb:
                stack.append((nx, cy - 1))
            if cy < h - 1 and image.pixel(nx, cy + 1) == target_rgb:
                stack.append((nx, cy + 1))


class FillTool(BaseTool):
    name = "fill"

    def on_press(self, image, pos, button):
        color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
        x, y = pos.x(), pos.y()
        if 0 <= x < image.width() and 0 <= y < image.height():
            _scanline_fill(image, x, y, color)
        return True

    def on_move(self, image, pos, button):
        return False

    def on_release(self, image, pos, button):
        return False
