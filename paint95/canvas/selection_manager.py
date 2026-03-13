"""
Selection manager: rectangular and free (lasso) selection.
"""
from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QPolygon, QRegion
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal, QObject


class SelectionManager(QObject):
    selection_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rect: QRect | None = None
        self._polygon: list[QPoint] = []
        self._mode: str = "rect"   # "rect" | "free"
        self._clipboard: QImage | None = None
        # offset for move
        self._move_origin: QPoint | None = None
        self._original_image: QImage | None = None

    # ------------------------------------------------------------------
    # Selection creation
    # ------------------------------------------------------------------
    def begin_rect(self, pos: QPoint) -> None:
        self._mode = "rect"
        self._rect = QRect(pos, pos)
        self._polygon.clear()

    def update_rect(self, pos: QPoint) -> None:
        if self._rect is not None:
            self._rect = QRect(self._rect.topLeft(), pos).normalized()

    def begin_free(self, pos: QPoint) -> None:
        self._mode = "free"
        self._polygon = [pos]
        self._rect = None

    def update_free(self, pos: QPoint) -> None:
        self._polygon.append(pos)

    def close_selection(self) -> None:
        if self._mode == "free" and len(self._polygon) > 2:
            poly = QPolygon(self._polygon)
            self._rect = poly.boundingRect()
        self.selection_changed.emit()

    def clear(self) -> None:
        self._rect = None
        self._polygon.clear()
        self._clipboard = None
        self.selection_changed.emit()

    @property
    def has_selection(self) -> bool:
        return self._rect is not None and not self._rect.isNull()

    @property
    def rect(self) -> QRect | None:
        return self._rect

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------
    def copy(self, image: QImage) -> None:
        if self._rect is None:
            return
        self._clipboard = image.copy(self._rect)

    def cut(self, image: QImage, bg: QColor) -> bool:
        if self._rect is None:
            return False
        self.copy(image)
        p = QPainter(image)
        p.fillRect(self._rect, bg)
        p.end()
        return True

    def paste(self, image: QImage) -> bool:
        if self._clipboard is None:
            return False
        p = QPainter(image)
        p.drawImage(QPoint(0, 0), self._clipboard)
        p.end()
        self._rect = QRect(QPoint(0, 0), self._clipboard.size())
        self.selection_changed.emit()
        return True

    def delete(self, image: QImage, bg: QColor) -> bool:
        if self._rect is None:
            return False
        p = QPainter(image)
        p.fillRect(self._rect, bg)
        p.end()
        return True

    def get_clipboard(self) -> QImage | None:
        return self._clipboard

    # ------------------------------------------------------------------
    # Overlay drawing (marching-ants dashes)
    # ------------------------------------------------------------------
    def draw_overlay(self, painter: QPainter, zoom: float) -> None:
        if not self.has_selection or self._rect is None:
            return
        scaled = QRect(
            round(self._rect.x() * zoom),
            round(self._rect.y() * zoom),
            round(self._rect.width() * zoom),
            round(self._rect.height() * zoom),
        )
        pen = QPen(QColor("#000000"), 1, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 4])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(scaled)
        pen2 = QPen(QColor("#FFFFFF"), 1, Qt.PenStyle.DashLine)
        pen2.setDashPattern([4, 4])
        pen2.setDashOffset(4)
        painter.setPen(pen2)
        painter.drawRect(scaled)
