"""Shape tools: Line, Rectangle, Ellipse, Polygon.

Preview mechanism
-----------------
Shapes are drawn on a *preview copy* during mouse drag so the canvas always
shows a live preview.  On mouse-release the preview is committed.

All tools delegate preview bookkeeping to canvas.begin_preview(),
canvas.restore_preview() and canvas.end_preview().
"""
from __future__ import annotations
import math
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPolygon
from PyQt6.QtCore import Qt, QPoint, QRect
from .base_tool import BaseTool


class FillMode:
    OUTLINE = "outline"
    FILLED = "filled"
    BOTH = "both"


# ── Line ─────────────────────────────────────────────────────────────────────

class LineTool(BaseTool):
    name = "Ligne"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self._x0 = self._y0 = 0
        self._active = False
        self._button = 1

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._x0, self._y0 = x, y
        self._active = True
        self._button = button
        canvas.save_undo()
        canvas.begin_preview()
        return False

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        x1, y1 = self._constrain(x, y, canvas.shift_held)
        canvas.restore_preview()
        self._draw(canvas.image, self._x0, self._y0, x1, y1,
                   self._fg if self._button == 1 else self._bg)
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        self._active = False
        x1, y1 = self._constrain(x, y, canvas.shift_held)
        canvas.restore_preview()
        self._draw(canvas.image, self._x0, self._y0, x1, y1,
                   self._fg if self._button == 1 else self._bg)
        canvas.end_preview()
        return True

    def _constrain(self, x: int, y: int, shift: bool) -> tuple[int, int]:
        if not shift:
            return x, y
        dx, dy = abs(x - self._x0), abs(y - self._y0)
        if dx > dy:
            return x, self._y0
        return self._x0, y

    def _draw(self, image, x0, y0, x1, y1, color: QColor) -> None:
        p = QPainter(image)
        p.setPen(QPen(color, self.thickness, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        p.drawLine(x0, y0, x1, y1)
        p.end()


# ── Rectangle ────────────────────────────────────────────────────────────────

class RectangleTool(BaseTool):
    name = "Rectangle"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self.fill_mode: str = FillMode.OUTLINE
        self._x0 = self._y0 = 0
        self._active = False
        self._button = 1

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._x0, self._y0 = x, y
        self._active = True
        self._button = button
        canvas.save_undo()
        canvas.begin_preview()
        return False

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        x1, y1 = self._constrain(x, y, canvas.shift_held)
        canvas.restore_preview()
        self._draw(canvas.image, self._x0, self._y0, x1, y1)
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        self._active = False
        x1, y1 = self._constrain(x, y, canvas.shift_held)
        canvas.restore_preview()
        self._draw(canvas.image, self._x0, self._y0, x1, y1)
        canvas.end_preview()
        return True

    def _constrain(self, x: int, y: int, shift: bool) -> tuple[int, int]:
        if not shift:
            return x, y
        size = min(abs(x - self._x0), abs(y - self._y0))
        return (self._x0 + size * (1 if x >= self._x0 else -1),
                self._y0 + size * (1 if y >= self._y0 else -1))

    def _draw(self, image, x0, y0, x1, y1) -> None:
        rect = QRect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        outline = self._fg if self._button == 1 else self._bg
        fill = self._bg if self._button == 1 else self._fg
        p = QPainter(image)
        if self.fill_mode == FillMode.OUTLINE:
            p.setPen(QPen(outline, self.thickness))
            p.setBrush(Qt.BrushStyle.NoBrush)
        elif self.fill_mode == FillMode.FILLED:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(fill))
        else:
            p.setPen(QPen(outline, self.thickness))
            p.setBrush(QBrush(fill))
        p.drawRect(rect)
        p.end()


# ── Ellipse ──────────────────────────────────────────────────────────────────

class EllipseTool(BaseTool):
    name = "Ellipse"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self.fill_mode: str = FillMode.OUTLINE
        self._x0 = self._y0 = 0
        self._active = False
        self._button = 1

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        self._x0, self._y0 = x, y
        self._active = True
        self._button = button
        canvas.save_undo()
        canvas.begin_preview()
        return False

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        x1, y1 = self._constrain(x, y, canvas.shift_held)
        canvas.restore_preview()
        self._draw(canvas.image, self._x0, self._y0, x1, y1)
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active:
            return False
        self._active = False
        x1, y1 = self._constrain(x, y, canvas.shift_held)
        canvas.restore_preview()
        self._draw(canvas.image, self._x0, self._y0, x1, y1)
        canvas.end_preview()
        return True

    def _constrain(self, x: int, y: int, shift: bool) -> tuple[int, int]:
        if not shift:
            return x, y
        size = min(abs(x - self._x0), abs(y - self._y0))
        return (self._x0 + size * (1 if x >= self._x0 else -1),
                self._y0 + size * (1 if y >= self._y0 else -1))

    def _draw(self, image, x0, y0, x1, y1) -> None:
        rect = QRect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        outline = self._fg if self._button == 1 else self._bg
        fill = self._bg if self._button == 1 else self._fg
        p = QPainter(image)
        if self.fill_mode == FillMode.OUTLINE:
            p.setPen(QPen(outline, self.thickness))
            p.setBrush(Qt.BrushStyle.NoBrush)
        elif self.fill_mode == FillMode.FILLED:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(fill))
        else:
            p.setPen(QPen(outline, self.thickness))
            p.setBrush(QBrush(fill))
        p.drawEllipse(rect)
        p.end()


# ── Polygon ──────────────────────────────────────────────────────────────────

class PolygonTool(BaseTool):
    name = "Polygone"

    def __init__(self) -> None:
        super().__init__()
        self.thickness: int = 1
        self.fill_mode: str = FillMode.OUTLINE
        self._points: list[tuple[int, int]] = []
        self._active = False

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        if button == 2:
            # Right-click closes the polygon
            if self._active and len(self._points) >= 2:
                self._commit(canvas)
            return True

        if not self._active:
            canvas.save_undo()
            canvas.begin_preview()
            self._active = True
            self._points = [(x, y)]
        else:
            self._points.append((x, y))
        return False

    def on_move(self, canvas, x: int, y: int, button: int) -> bool:
        if not self._active or not self._points:
            return False
        canvas.restore_preview()
        self._draw_wip(canvas.image, self._points + [(x, y)])
        return True

    def on_release(self, canvas, x: int, y: int, button: int) -> bool:
        return False

    def _commit(self, canvas) -> None:
        self._active = False
        canvas.restore_preview()
        self._render_polygon(canvas.image, self._points, closed=True)
        self._points = []
        canvas.end_preview()

    def _draw_wip(self, image, points: list[tuple[int, int]]) -> None:
        """Draw work-in-progress segments (not closed)."""
        self._render_polygon(image, points, closed=False)

    def _render_polygon(self, image, points: list[tuple[int, int]],
                        closed: bool) -> None:
        if len(points) < 2:
            return
        outline = self._fg
        fill = self._bg
        qpts = QPolygon([QPoint(x, y) for x, y in points])
        p = QPainter(image)
        if closed:
            if self.fill_mode == FillMode.OUTLINE:
                p.setPen(QPen(outline, self.thickness))
                p.setBrush(Qt.BrushStyle.NoBrush)
            elif self.fill_mode == FillMode.FILLED:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(fill))
            else:
                p.setPen(QPen(outline, self.thickness))
                p.setBrush(QBrush(fill))
            p.drawPolygon(qpts)
        else:
            p.setPen(QPen(outline, self.thickness))
            p.drawPolyline(qpts)
        p.end()
