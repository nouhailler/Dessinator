"""
Colour palette widget — 28-colour grid + active colour display.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QFrame, QSizePolicy
from PyQt6.QtGui import QColor, QPainter, QPen, QMouseEvent
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal

from ..color.palette_manager import PaletteManager
from ..color.color_dialog import ColorPickerDialog


class ColorSwatch(QWidget):
    """A single colour square in the palette."""
    clicked = pyqtSignal(QColor, int)   # color, button (1=left, 2=right)

    def __init__(self, color: QColor, parent=None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedSize(16, 16)
        self.setToolTip(color.name())

    def set_color(self, c: QColor) -> None:
        self._color = c
        self.setToolTip(c.name())
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), self._color)
        p.setPen(QPen(QColor("#888888"), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        p.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._color, 1)
        elif event.button() == Qt.MouseButton.RightButton:
            self.clicked.emit(self._color, 2)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        dlg = ColorPickerDialog(self._color, self)
        if dlg.exec():
            self.set_color(dlg.selected_color())
            self.clicked.emit(self._color, 1)


class ActiveColorDisplay(QWidget):
    """Shows foreground (front) and background (back) colour boxes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._fg = QColor("#000000")
        self._bg = QColor("#FFFFFF")
        self.setFixedSize(42, 42)
        self.setToolTip("Couleur avant-plan / arrière-plan")

    def set_fg(self, c: QColor) -> None:
        self._fg = c
        self.update()

    def set_bg(self, c: QColor) -> None:
        self._bg = c
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        # background box (offset)
        bg_rect = QRect(12, 12, 26, 26)
        p.fillRect(bg_rect, self._bg)
        p.setPen(QPen(QColor("#555555"), 1))
        p.drawRect(bg_rect)
        # foreground box
        fg_rect = QRect(4, 4, 26, 26)
        p.fillRect(fg_rect, self._fg)
        p.setPen(QPen(QColor("#555555"), 1))
        p.drawRect(fg_rect)
        p.end()


class PaletteWidget(QWidget):
    """Bottom palette bar."""

    fg_changed = pyqtSignal(QColor)
    bg_changed = pyqtSignal(QColor)

    def __init__(self, manager: PaletteManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._swatches: list[ColorSwatch] = []

        main = QHBoxLayout(self)
        main.setContentsMargins(4, 2, 4, 2)
        main.setSpacing(4)

        self._active_display = ActiveColorDisplay()
        main.addWidget(self._active_display)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(1)
        grid.setContentsMargins(0, 0, 0, 0)

        colors = manager.colors
        for i, color in enumerate(colors):
            swatch = ColorSwatch(color)
            swatch.clicked.connect(self._on_swatch_click)
            self._swatches.append(swatch)
            row = i // 14
            col = i % 14
            grid.addWidget(swatch, row, col)

        main.addWidget(grid_widget)
        main.addStretch()

        self._update_display()

    def _on_swatch_click(self, color: QColor, button: int) -> None:
        if button == 1:
            self._manager.foreground = color
            self.fg_changed.emit(color)
        else:
            self._manager.background = color
            self.bg_changed.emit(color)
        self._update_display()

    def _update_display(self) -> None:
        self._active_display.set_fg(self._manager.foreground)
        self._active_display.set_bg(self._manager.background)

    def set_fg(self, color: QColor) -> None:
        self._manager.foreground = color
        self._update_display()

    def set_bg(self, color: QColor) -> None:
        self._manager.background = color
        self._update_display()
