"""
Colour picker (pipette) tool.
Left-click  → sets foreground colour.
Right-click → sets background colour.
"""
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtCore import pyqtSignal, QObject
from .base import BaseTool


class PipetteTool(BaseTool, QObject):
    name = "pipette"

    # Emit (color, is_foreground)
    color_picked = pyqtSignal(QColor, bool)

    def __init__(self) -> None:
        BaseTool.__init__(self)
        QObject.__init__(self)

    def on_press(self, image: QImage, pos: QPoint, button: int) -> bool:
        x, y = pos.x(), pos.y()
        if 0 <= x < image.width() and 0 <= y < image.height():
            color = QColor(image.pixel(x, y))
            is_fg = (button == Qt.MouseButton.LeftButton)
            self.color_picked.emit(color, is_fg)
        return False
