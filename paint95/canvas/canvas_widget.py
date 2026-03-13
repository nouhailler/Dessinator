"""
Canvas widget: displays the QImage with zoom, grid, and selection overlay.
Handles all mouse and keyboard events, then delegates to DrawingEngine.
"""
from PyQt6.QtWidgets import QWidget, QSizePolicy, QInputDialog, QFontDialog
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QMouseEvent, QWheelEvent,
    QKeyEvent, QCursor, QImage,
)
from PyQt6.QtCore import (
    Qt, QPoint, QRect, QSize, pyqtSignal, QObject,
)

from .drawing_engine import DrawingEngine
from .selection_manager import SelectionManager
from ..tools.base import BaseTool
from ..tools.pencil import PencilTool
from ..tools.brush import BrushTool
from ..tools.eraser import EraserTool
from ..tools.spray import SprayTool
from ..tools.fill import FillTool
from ..tools.pipette import PipetteTool
from ..tools.shapes import LineTool, RectangleTool, EllipseTool, PolygonTool, CurveTool, TextTool

ZOOM_LEVELS = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
GRID_MIN_ZOOM = 4.0


class _SelectRectTool(BaseTool):
    name = "select_rect"

class _SelectFreeTool(BaseTool):
    name = "select_free"

class CanvasWidget(QWidget):
    """The central drawing surface."""

    cursor_moved = pyqtSignal(int, int)   # x, y in image coordinates
    tool_changed = pyqtSignal(str)
    zoom_changed = pyqtSignal(float)

    def __init__(self, engine: DrawingEngine, parent=None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._engine.image_changed.connect(self.update)

        self._selection = SelectionManager(self)
        self._selection.selection_changed.connect(self.update)

        self._zoom: float = 1.0
        self._show_grid: bool = False
        self._offset = QPoint(0, 0)

        # All tools
        self._pencil = PencilTool()
        self._brush = BrushTool()
        self._eraser = EraserTool()
        self._spray = SprayTool()
        self._fill = FillTool()
        self._pipette = PipetteTool()
        self._line = LineTool()
        self._rect_tool = RectangleTool()
        self._ellipse = EllipseTool()
        self._polygon = PolygonTool()
        self._curve = CurveTool()
        self._text_tool = TextTool()

        self._pipette.color_picked.connect(self._on_color_picked)

        self._all_tools: dict[str, BaseTool] = {
            "pencil": self._pencil,
            "brush": self._brush,
            "eraser": self._eraser,
            "spray": self._spray,
            "fill": self._fill,
            "pipette": self._pipette,
            "line": self._line,
            "rectangle": self._rect_tool,
            "ellipse": self._ellipse,
            "polygon": self._polygon,
            "curve": self._curve,
            "text": self._text_tool,
            "select_rect": _SelectRectTool(),
            "select_free": _SelectFreeTool(),
        }

        self._active_tool: BaseTool = self._pencil
        self._engine.set_tool(self._active_tool)

        self._fg = QColor("#000000")
        self._bg = QColor("#FFFFFF")
        self._update_tool_colors()

        self._dragging = False
        self._last_btn: int = Qt.MouseButton.LeftButton
        self._selecting = False
        self._sel_mode = "rect"

        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def engine(self) -> DrawingEngine:
        return self._engine

    @property
    def selection(self) -> SelectionManager:
        return self._selection

    def set_tool(self, name: str) -> None:
        tool = self._all_tools.get(name)
        if tool is None:
            return
        self._active_tool = tool
        self._engine.set_tool(tool)
        self.tool_changed.emit(name)
        # Reset polygon if switching away
        if name != "polygon":
            self._polygon._points.clear()

    def set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.1, min(8.0, zoom))
        self.update()
        self.zoom_changed.emit(self._zoom)

    def zoom_in(self) -> None:
        idx = self._nearest_zoom_idx()
        if idx < len(ZOOM_LEVELS) - 1:
            self.set_zoom(ZOOM_LEVELS[idx + 1])

    def zoom_out(self) -> None:
        idx = self._nearest_zoom_idx()
        if idx > 0:
            self.set_zoom(ZOOM_LEVELS[idx - 1])

    def _nearest_zoom_idx(self) -> int:
        diffs = [abs(z - self._zoom) for z in ZOOM_LEVELS]
        return diffs.index(min(diffs))

    def set_colors(self, fg: QColor, bg: QColor) -> None:
        self._fg = fg
        self._bg = bg
        self._update_tool_colors()

    def set_show_grid(self, show: bool) -> None:
        self._show_grid = show
        self.update()

    def get_active_tool_name(self) -> str:
        return self._active_tool.name

    def get_brush(self) -> BrushTool:
        return self._brush

    def get_eraser(self) -> EraserTool:
        return self._eraser

    def get_spray(self) -> SprayTool:
        return self._spray

    def get_line(self) -> LineTool:
        return self._line

    def get_rect_tool(self) -> RectangleTool:
        return self._rect_tool

    def get_ellipse(self) -> EllipseTool:
        return self._ellipse

    def get_polygon(self) -> PolygonTool:
        return self._polygon

    # ------------------------------------------------------------------
    # Colour picked by pipette
    # ------------------------------------------------------------------
    color_picked = pyqtSignal(QColor, bool)

    def _on_color_picked(self, color: QColor, is_fg: bool) -> None:
        self.color_picked.emit(color, is_fg)

    def _update_tool_colors(self) -> None:
        for tool in self._all_tools.values():
            tool.set_colors(self._fg, self._bg)

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def _to_image(self, widget_pos: QPoint) -> QPoint:
        x = (widget_pos.x() - self._offset.x()) / self._zoom
        y = (widget_pos.y() - self._offset.y()) / self._zoom
        return QPoint(int(x), int(y))

    def _canvas_rect(self) -> QRect:
        img = self._engine.image
        w = round(img.width() * self._zoom)
        h = round(img.height() * self._zoom)
        return QRect(self._offset, QSize(w, h))

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self._zoom < 1.0)

        img = self._engine.image
        canvas_rect = self._canvas_rect()

        # Checkerboard background
        painter.fillRect(self.rect(), QColor("#808080"))

        # Draw image
        painter.drawImage(canvas_rect, img)

        # Pixel grid
        if self._show_grid and self._zoom >= GRID_MIN_ZOOM:
            self._draw_grid(painter, canvas_rect, img.width(), img.height())

        # Selection overlay
        painter.save()
        painter.translate(self._offset)
        self._selection.draw_overlay(painter, self._zoom)
        painter.restore()

        painter.end()

    def _draw_grid(self, painter: QPainter, canvas_rect: QRect,
                   img_w: int, img_h: int) -> None:
        pen = QPen(QColor(0, 0, 0, 80), 1)
        painter.setPen(pen)
        ox, oy = canvas_rect.x(), canvas_rect.y()
        for ix in range(img_w + 1):
            x = ox + round(ix * self._zoom)
            painter.drawLine(x, oy, x, oy + canvas_rect.height())
        for iy in range(img_h + 1):
            y = oy + round(iy * self._zoom)
            painter.drawLine(ox, y, ox + canvas_rect.width(), y)

    # ------------------------------------------------------------------
    # Size hint
    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        img = self._engine.image
        return QSize(round(img.width() * self._zoom) + 40,
                     round(img.height() * self._zoom) + 40)

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = self._to_image(event.pos())
        btn = event.button()
        self._last_btn = btn

        if self._active_tool.name == "text":
            self._text_tool.on_press(self._engine.image, pos, btn)
            self._show_text_dialog(pos)
            return

        if self._active_tool.name == "polygon":
            # single click adds a point
            self._engine.save_state()
            self._polygon.add_point(self._engine.image, pos, btn)
            self.update()
            return

        if self._active_tool.name == "select_rect":
            self._selection.begin_rect(pos)
            self._selecting = True
        elif self._active_tool.name == "select_free":
            self._selection.begin_free(pos)
            self._selecting = True
        else:
            self._dragging = True
            self._engine.press(pos, btn)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        pos = self._to_image(event.pos())
        if self._active_tool.name == "polygon":
            self._polygon.close_polygon(self._engine.image)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = self._to_image(event.pos())
        self.cursor_moved.emit(pos.x(), pos.y())
        if self._selecting:
            if self._active_tool.name == "select_rect":
                self._selection.update_rect(pos)
            else:
                self._selection.update_free(pos)
            self.update()
        elif self._dragging:
            btn = event.buttons()
            self._engine.move(pos, btn)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pos = self._to_image(event.pos())
        if self._selecting:
            self._selection.close_selection()
            self._selecting = False
            self.update()
        elif self._dragging:
            self._engine.release(pos, event.button())
            self._dragging = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Shift:
            self._line._constrain = True
            self._rect_tool._constrain = True
            self._ellipse._constrain = True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Shift:
            self._line._constrain = False
            self._rect_tool._constrain = False
            self._ellipse._constrain = False
        super().keyReleaseEvent(event)

    # ------------------------------------------------------------------
    # Text dialog
    # ------------------------------------------------------------------
    def _show_text_dialog(self, pos: QPoint) -> None:
        font_dlg = QFontDialog(QFont("Arial", 12), self)
        font_dlg.setWindowTitle("Police de caractères")
        if not font_dlg.exec():
            return
        font = font_dlg.selectedFont()

        text, ok = QInputDialog.getText(self, "Saisie de texte", "Texte :")
        if not ok or not text:
            return

        self._engine.save_state()
        painter = QPainter(self._engine.image)
        painter.setFont(font)
        painter.setPen(self._fg)
        painter.drawText(pos, text)
        painter.end()
        self.update()
