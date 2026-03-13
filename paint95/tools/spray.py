"""
Spray / airbrush tool — random pixel distribution inside a circle.
"""
import random
import math
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import QPoint, Qt
from .base import BaseTool


class SprayTool(BaseTool):
    name = "spray"

    def __init__(self) -> None:
        super().__init__()
        self.radius: int = 15
        self.density: int = 30   # pixels per event

    def _spray(self, image: QImage, pos: QPoint, color: QColor) -> None:
        w, h = image.width(), image.height()
        rgb = color.rgb()
        for _ in range(self.density):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, self.radius)
            x = int(pos.x() + r * math.cos(angle))
            y = int(pos.y() + r * math.sin(angle))
            if 0 <= x < w and 0 <= y < h:
                image.setPixel(x, y, rgb)

    def on_press(self, image, pos, button):
        color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
        self._active_color = color
        self._spray(image, pos, color)
        return True

    def on_move(self, image, pos, button):
        self._spray(image, pos, self._active_color)
        return True

    def on_release(self, image, pos, button):
        return False
