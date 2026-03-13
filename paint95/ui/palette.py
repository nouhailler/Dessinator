"""Colour palette widget — FG/BG indicators + 28-colour swatch grid."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QColorDialog, QHBoxLayout, QSizePolicy


class ColorSquares(QWidget):
    """Two overlapping squares showing foreground (front) and background (back)."""

    fg_changed = pyqtSignal(QColor)
    bg_changed = pyqtSignal(QColor)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._fg = QColor("#000000")
        self._bg = QColor("#ffffff")
        self.setFixedSize(52, 44)
        self.setToolTip("Clic gauche : couleur avant-plan\nClic droit : couleur arrière-plan")

    def set_fg(self, color: QColor) -> None:
        self._fg = color
        self.update()

    def set_bg(self, color: QColor) -> None:
        self._bg = color
        self.update()

    def fg(self) -> QColor:
        return self._fg

    def bg(self) -> QColor:
        return self._bg

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        # background square (bottom-right)
        p.setPen(QPen(Qt.GlobalColor.black, 1))
        p.setBrush(QBrush(self._bg))
        p.drawRect(16, 14, 28, 24)
        # foreground square (top-left)
        p.setBrush(QBrush(self._fg))
        p.drawRect(4, 4, 28, 24)
        p.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            color = QColorDialog.getColor(self._fg, self, "Couleur avant-plan")
            if color.isValid():
                self._fg = color
                self.update()
                self.fg_changed.emit(color)
        elif event.button() == Qt.MouseButton.RightButton:
            color = QColorDialog.getColor(self._bg, self, "Couleur arrière-plan")
            if color.isValid():
                self._bg = color
                self.update()
                self.bg_changed.emit(color)


class SwatchGrid(QWidget):
    """14×2 grid of colour swatches."""

    color_left_clicked = pyqtSignal(QColor)
    color_right_clicked = pyqtSignal(QColor)

    SWATCH = 20   # size of each swatch in pixels
    COLS = 14

    def __init__(self, colors: list[QColor], parent=None) -> None:
        super().__init__(parent)
        self._colors = colors
        rows = (len(colors) + self.COLS - 1) // self.COLS
        self.setFixedSize(self.COLS * self.SWATCH + 2,
                          rows * self.SWATCH + 2)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        for i, color in enumerate(self._colors):
            col = i % self.COLS
            row = i // self.COLS
            x = col * self.SWATCH + 1
            y = row * self.SWATCH + 1
            p.fillRect(x, y, self.SWATCH - 1, self.SWATCH - 1, color)
            p.setPen(QPen(QColor(90, 90, 90), 0))
            p.drawRect(x, y, self.SWATCH - 2, self.SWATCH - 2)
        p.end()

    def _color_at(self, x: int, y: int) -> QColor | None:
        col = (x - 1) // self.SWATCH
        row = (y - 1) // self.SWATCH
        idx = row * self.COLS + col
        if 0 <= idx < len(self._colors):
            return self._colors[idx]
        return None

    def mousePressEvent(self, event) -> None:
        color = self._color_at(int(event.position().x()),
                               int(event.position().y()))
        if color is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.color_left_clicked.emit(color)
        elif event.button() == Qt.MouseButton.RightButton:
            self.color_right_clicked.emit(color)

    def mouseDoubleClickEvent(self, event) -> None:
        """Double-click opens a custom colour dialog."""
        color = self._color_at(int(event.position().x()),
                               int(event.position().y()))
        base = color if color else QColor("#ffffff")
        chosen = QColorDialog.getColor(base, self, "Choisir une couleur")
        if chosen.isValid():
            col = (int(event.position().x()) - 1) // self.SWATCH
            row = (int(event.position().y()) - 1) // self.SWATCH
            idx = row * self.COLS + col
            if 0 <= idx < len(self._colors):
                self._colors[idx] = chosen
                self.update()
                if event.button() == Qt.MouseButton.LeftButton:
                    self.color_left_clicked.emit(chosen)


class PaletteWidget(QWidget):
    """Full palette bar: FG/BG squares + swatch grid."""

    fg_changed = pyqtSignal(QColor)
    bg_changed = pyqtSignal(QColor)

    def __init__(self, palette_manager, parent=None) -> None:
        super().__init__(parent)
        self._pm = palette_manager
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self._squares = ColorSquares()
        self._squares.set_fg(self._pm.foreground)
        self._squares.set_bg(self._pm.background)
        self._squares.fg_changed.connect(self._on_fg)
        self._squares.bg_changed.connect(self._on_bg)
        layout.addWidget(self._squares, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._grid = SwatchGrid(self._pm.colors)
        self._grid.color_left_clicked.connect(self._on_fg)
        self._grid.color_right_clicked.connect(self._on_bg)
        layout.addWidget(self._grid, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()

    def _on_fg(self, color: QColor) -> None:
        self._pm.foreground = color
        self._squares.set_fg(color)
        self.fg_changed.emit(color)

    def _on_bg(self, color: QColor) -> None:
        self._pm.background = color
        self._squares.set_bg(color)
        self.bg_changed.emit(color)

    def set_fg(self, color: QColor) -> None:
        self._on_fg(color)

    def set_bg(self, color: QColor) -> None:
        self._on_bg(color)
