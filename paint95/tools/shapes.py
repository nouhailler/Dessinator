"""
Shape tools: Line, Rectangle, Ellipse, Polygon, Curve (3-point Bézier).
"""
from PyQt6.QtGui import (
    QImage, QPainter, QPen, QBrush, QColor,
    QPolygon, QPainterPath,
)
from PyQt6.QtCore import QPoint, QRect, Qt, QLine
from .base import BaseTool


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_painter(image: QImage, color: QColor, thickness: int,
                  fill: QColor | None = None) -> QPainter:
    p = QPainter(image)
    pen = QPen(color, thickness, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    if fill is not None:
        p.setBrush(QBrush(fill))
    else:
        p.setBrush(Qt.BrushStyle.NoBrush)
    return p


def _constrain(p0: QPoint, p1: QPoint) -> QPoint:
    """Constrain to nearest 45° direction (for Shift)."""
    dx = p1.x() - p0.x()
    dy = p1.y() - p0.y()
    if abs(dx) >= abs(dy):
        return QPoint(p1.x(), p0.y() + (abs(dx) if dy >= 0 else -abs(dx)))
    else:
        return QPoint(p0.x() + (abs(dy) if dx >= 0 else -abs(dy)), p1.y())


# ── Line ─────────────────────────────────────────────────────────────────────

class LineTool(BaseTool):
    name = "line"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self._start: QPoint | None = None
        self._preview_end: QPoint | None = None
        self._constrain: bool = False
        self._committed: QImage | None = None

    def on_press(self, image, pos, button):
        self._start = pos
        self._preview_end = pos
        self._active_color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
        self._committed = image.copy()
        return False

    def on_move(self, image, pos, button):
        if self._start is None or self._committed is None:
            return False
        end = _constrain(self._start, pos) if self._constrain else pos
        self._preview_end = end
        # Restore committed state, draw preview
        image.swap(self._committed.copy())
        p = _make_painter(image, self._active_color, self.thickness)
        p.drawLine(self._start, end)
        p.end()
        return True

    def on_release(self, image, pos, button):
        if self._start is None:
            return False
        end = _constrain(self._start, pos) if self._constrain else pos
        image.swap(self._committed.copy())
        p = _make_painter(image, self._active_color, self.thickness)
        p.drawLine(self._start, end)
        p.end()
        self._start = None
        self._committed = None
        return True


# ── Rectangle ────────────────────────────────────────────────────────────────

class FillMode:
    OUTLINE = "outline"
    FILLED = "filled"
    BOTH = "both"


class RectangleTool(BaseTool):
    name = "rectangle"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self.fill_mode: str = FillMode.OUTLINE
        self._start: QPoint | None = None
        self._constrain: bool = False
        self._committed: QImage | None = None

    def _get_rect(self, p0: QPoint, p1: QPoint) -> QRect:
        if self._constrain:
            side = min(abs(p1.x() - p0.x()), abs(p1.y() - p0.y()))
            x1 = p0.x() + (side if p1.x() >= p0.x() else -side)
            y1 = p0.y() + (side if p1.y() >= p0.y() else -side)
            p1 = QPoint(x1, y1)
        return QRect(p0, p1).normalized()

    def _draw(self, image: QImage, rect: QRect) -> None:
        stroke = self._active_stroke
        fill = self._active_fill
        p = _make_painter(image, stroke, self.thickness,
                          fill if self.fill_mode != FillMode.OUTLINE else None)
        if self.fill_mode == FillMode.OUTLINE:
            p.drawRect(rect)
        elif self.fill_mode == FillMode.FILLED:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(fill))
            p.drawRect(rect)
        else:  # BOTH
            p.drawRect(rect)
        p.end()

    def on_press(self, image, pos, button):
        self._start = pos
        if button == Qt.MouseButton.LeftButton:
            self._active_stroke = self.foreground
            self._active_fill = self.background
        else:
            self._active_stroke = self.background
            self._active_fill = self.foreground
        self._committed = image.copy()
        return False

    def on_move(self, image, pos, button):
        if self._start is None or self._committed is None:
            return False
        rect = self._get_rect(self._start, pos)
        image.swap(self._committed.copy())
        self._draw(image, rect)
        return True

    def on_release(self, image, pos, button):
        if self._start is None:
            return False
        rect = self._get_rect(self._start, pos)
        image.swap(self._committed.copy())
        self._draw(image, rect)
        self._start = None
        self._committed = None
        return True


# ── Ellipse ──────────────────────────────────────────────────────────────────

class EllipseTool(RectangleTool):
    name = "ellipse"

    def _draw(self, image: QImage, rect: QRect) -> None:
        stroke = self._active_stroke
        fill = self._active_fill
        p = _make_painter(image, stroke, self.thickness,
                          fill if self.fill_mode != FillMode.OUTLINE else None)
        if self.fill_mode == FillMode.OUTLINE:
            p.drawEllipse(rect)
        elif self.fill_mode == FillMode.FILLED:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(fill))
            p.drawEllipse(rect)
        else:
            p.drawEllipse(rect)
        p.end()


# ── Polygon ──────────────────────────────────────────────────────────────────

class PolygonTool(BaseTool):
    """Click to add vertices; double-click to close the polygon."""
    name = "polygon"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self.fill_mode: str = FillMode.OUTLINE
        self._points: list[QPoint] = []
        self._active_color = QColor("#000000")
        self._committed: QImage | None = None

    def on_press(self, image, pos, button):
        return False

    def on_move(self, image, pos, button):
        if not self._points or self._committed is None:
            return False
        image.swap(self._committed.copy())
        self._draw_in_progress(image, pos)
        return True

    def on_release(self, image, pos, button):
        return False

    # Called externally by the canvas on single click
    def add_point(self, image: QImage, pos: QPoint, button: int) -> bool:
        if not self._points:
            self._active_color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
            self._committed = image.copy()
        self._points.append(pos)
        self._draw_in_progress(image, pos)
        return True

    # Called on double-click
    def close_polygon(self, image: QImage) -> bool:
        if len(self._points) >= 3:
            poly = QPolygon(self._points)
            p = _make_painter(image, self._active_color, self.thickness)
            if self.fill_mode != FillMode.OUTLINE:
                p.setBrush(QBrush(self.background))
            p.drawPolygon(poly)
            p.end()
        self._points.clear()
        self._committed = None
        return True

    def _draw_in_progress(self, image: QImage, cursor: QPoint) -> None:
        if len(self._points) < 1:
            return
        p = _make_painter(image, self._active_color, self.thickness)
        for i in range(1, len(self._points)):
            p.drawLine(self._points[i - 1], self._points[i])
        p.drawLine(self._points[-1], cursor)
        p.end()


# ── Curve (quadratic Bézier, 3-point) ────────────────────────────────────────

class CurveTool(BaseTool):
    """
    Step 1: drag to set start and end.
    Step 2: click to set the control point → curve is committed.
    """
    name = "curve"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self._step: int = 0          # 0 = idle, 1 = end chosen, 2 = done
        self._p0: QPoint | None = None
        self._p1: QPoint | None = None
        self._ctrl: QPoint | None = None
        self._active_color = QColor("#000000")
        self._committed: QImage | None = None

    def on_press(self, image, pos, button):
        if self._step == 0:
            self._p0 = pos
            self._active_color = self.foreground if button == Qt.MouseButton.LeftButton else self.background
            self._committed = image.copy()
            self._step = 1
        elif self._step == 1:
            # Control point
            self._ctrl = pos
            self._commit(image)
            self._step = 0
        return True

    def on_move(self, image, pos, button):
        if self._step == 1 and self._p0 is not None and self._committed is not None:
            self._p1 = pos
            image.swap(self._committed.copy())
            p = _make_painter(image, self._active_color, self.thickness)
            p.drawLine(self._p0, pos)
            p.end()
            return True
        return False

    def on_release(self, image, pos, button):
        if self._step == 1:
            self._p1 = pos
        return False

    def _commit(self, image: QImage) -> None:
        if self._p0 is None or self._p1 is None or self._ctrl is None:
            return
        image.swap(self._committed.copy())
        path = QPainterPath()
        path.moveTo(self._p0)
        path.quadTo(self._ctrl, self._p1)
        p = QPainter(image)
        pen = QPen(self._active_color, self.thickness, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.end()
        self._committed = None


# ── Text ──────────────────────────────────────────────────────────────────────

class TextTool(BaseTool):
    """Positions a text anchor; actual rendering is done by the canvas."""
    name = "text"

    def __init__(self) -> None:
        super().__init__()
        self._anchor: QPoint | None = None

    def on_press(self, image, pos, button):
        self._anchor = pos
        return False

    @property
    def anchor(self) -> QPoint | None:
        return self._anchor
