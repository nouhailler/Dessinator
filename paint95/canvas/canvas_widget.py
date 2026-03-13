"""Core raster canvas widget.

Responsibilities
----------------
* Holds the current QImage (ARGB32).
* Scales the image for display according to zoom level.
* Converts screen ↔ image coordinates.
* Dispatches mouse events to the active tool.
* Manages the shape-preview buffer.
* Manages the selection rectangle overlay.
* Proxies undo/redo to UndoManager.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QSizePolicy

from history.undo_manager import UndoManager
from file_io.image_loader import ImageLoader

ZOOM_LEVELS = [10, 25, 50, 75, 100, 150, 200, 400, 800]
DEFAULT_ZOOM_IDX = 4  # 100 %


class CanvasWidget(QWidget):
    """The drawing surface — a fixed-size QWidget backed by a QImage."""

    mouse_moved = pyqtSignal(int, int)   # image-space x, y
    zoom_changed = pyqtSignal(int)       # new zoom %

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # ── image state ─────────────────────────────────────────────────────
        self._image: QImage = ImageLoader.new_image(800, 600)
        self._saved_image: QImage | None = None   # for shape preview

        # ── clipboard ───────────────────────────────────────────────────────
        self._clipboard: QImage | None = None

        # ── selection overlay (image coordinates) ───────────────────────────
        self._selection: QRect | None = None

        # ── zoom ────────────────────────────────────────────────────────────
        self._zoom_idx = DEFAULT_ZOOM_IDX
        self._zoom = ZOOM_LEVELS[DEFAULT_ZOOM_IDX]

        # ── grid ────────────────────────────────────────────────────────────
        self._show_grid = False

        # ── input state ─────────────────────────────────────────────────────
        self.shift_held = False
        self._button_held = 0

        # ── tool & colours ──────────────────────────────────────────────────
        self._tool = None
        self._fg = QColor("#000000")
        self._bg = QColor("#ffffff")

        # ── undo ────────────────────────────────────────────────────────────
        self._undo = UndoManager()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._apply_size()

    # ═══════════════════════════════════════════════════════════════════════
    # Public image API
    # ═══════════════════════════════════════════════════════════════════════

    @property
    def image(self) -> QImage:
        return self._image

    def new_image(self, width: int, height: int,
                  bg: QColor = QColor("#ffffff")) -> None:
        self._image = ImageLoader.new_image(width, height, bg.name())
        self._saved_image = None
        self._selection = None
        self._undo.clear()
        self._apply_size()
        self.update()

    def load_image(self, image: QImage) -> None:
        self._image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self._saved_image = None
        self._selection = None
        self._undo.clear()
        self._apply_size()
        self.update()

    def replace_image(self, image: QImage) -> None:
        """Replace the underlying image directly (e.g. after flood-fill)."""
        self._image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self._saved_image = None
        self.update()

    # ── shape preview ───────────────────────────────────────────────────────

    def begin_preview(self) -> None:
        """Save image state before drawing a shape (preview begins)."""
        self._saved_image = self._image.copy()

    def restore_preview(self) -> None:
        """Restore image to the saved state (redraw preview from scratch)."""
        if self._saved_image is not None:
            self._image = self._saved_image.copy()

    def end_preview(self) -> None:
        """Commit current image; discard saved state."""
        self._saved_image = None
        self.update()

    # ── undo / redo ─────────────────────────────────────────────────────────

    def save_undo(self) -> None:
        self._undo.push(self._image)

    def undo(self) -> None:
        result = self._undo.undo(self._image)
        if result is not None:
            self._image = result
            self._saved_image = None
            self.update()

    def redo(self) -> None:
        result = self._undo.redo(self._image)
        if result is not None:
            self._image = result
            self._saved_image = None
            self.update()

    def can_undo(self) -> bool:
        return self._undo.can_undo()

    def can_redo(self) -> bool:
        return self._undo.can_redo()

    # ── selection ───────────────────────────────────────────────────────────

    def set_selection(self, rect: QRect | None) -> None:
        self._selection = rect
        self.update()

    def copy_selection(self) -> None:
        if self._selection and not self._selection.isEmpty():
            self._clipboard = self._image.copy(self._selection)

    def cut_selection(self) -> None:
        if self._selection and not self._selection.isEmpty():
            self._clipboard = self._image.copy(self._selection)
            self.save_undo()
            p = QPainter(self._image)
            p.fillRect(self._selection, self._bg)
            p.end()
            self.update()

    def paste(self) -> None:
        if self._clipboard is not None:
            self.save_undo()
            p = QPainter(self._image)
            p.drawImage(0, 0, self._clipboard)
            p.end()
            self._selection = None
            self.update()

    def delete_selection(self) -> None:
        if self._selection and not self._selection.isEmpty():
            self.save_undo()
            p = QPainter(self._image)
            p.fillRect(self._selection, self._bg)
            p.end()
            self._selection = None
            self.update()

    # ── image operations ────────────────────────────────────────────────────

    def invert_colors(self) -> None:
        self.save_undo()
        self._image.invertPixels()
        self.update()

    def flip_horizontal(self) -> None:
        self.save_undo()
        self._image = self._image.mirrored(True, False)
        self.update()

    def flip_vertical(self) -> None:
        self.save_undo()
        self._image = self._image.mirrored(False, True)
        self.update()

    # ═══════════════════════════════════════════════════════════════════════
    # Zoom
    # ═══════════════════════════════════════════════════════════════════════

    @property
    def zoom(self) -> int:
        return self._zoom

    def zoom_in(self) -> None:
        if self._zoom_idx < len(ZOOM_LEVELS) - 1:
            self._zoom_idx += 1
            self._set_zoom(ZOOM_LEVELS[self._zoom_idx])

    def zoom_out(self) -> None:
        if self._zoom_idx > 0:
            self._zoom_idx -= 1
            self._set_zoom(ZOOM_LEVELS[self._zoom_idx])

    def set_zoom_level(self, zoom: int) -> None:
        if zoom in ZOOM_LEVELS:
            self._zoom_idx = ZOOM_LEVELS.index(zoom)
            self._set_zoom(zoom)

    def _set_zoom(self, zoom: int) -> None:
        self._zoom = zoom
        self._apply_size()
        self.zoom_changed.emit(zoom)
        self.update()

    def _apply_size(self) -> None:
        w = max(1, int(self._image.width() * self._zoom / 100))
        h = max(1, int(self._image.height() * self._zoom / 100))
        self.setFixedSize(w, h)

    # ── grid ────────────────────────────────────────────────────────────────

    @property
    def show_grid(self) -> bool:
        return self._show_grid

    def toggle_grid(self) -> None:
        self._show_grid = not self._show_grid
        self.update()

    # ═══════════════════════════════════════════════════════════════════════
    # Tool & colour management
    # ═══════════════════════════════════════════════════════════════════════

    def set_tool(self, tool) -> None:
        self._tool = tool
        if tool:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def update_colors(self, fg: QColor, bg: QColor) -> None:
        self._fg = fg
        self._bg = bg

    # ═══════════════════════════════════════════════════════════════════════
    # Coordinate helpers
    # ═══════════════════════════════════════════════════════════════════════

    def screen_to_image(self, sx: float, sy: float) -> tuple[int, int]:
        ix = int(sx * 100 / self._zoom)
        iy = int(sy * 100 / self._zoom)
        return ix, iy

    # ═══════════════════════════════════════════════════════════════════════
    # Painting
    # ═══════════════════════════════════════════════════════════════════════

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        w = int(self._image.width() * self._zoom / 100)
        h = int(self._image.height() * self._zoom / 100)

        # ── scaled image ────────────────────────────────────────────────────
        p.drawImage(QRect(0, 0, w, h), self._image)

        # ── pixel grid (zoom ≥ 200 %) ────────────────────────────────────────
        if self._show_grid and self._zoom >= 200:
            self._paint_grid(p, w, h)

        # ── selection overlay ────────────────────────────────────────────────
        if self._selection and not self._selection.isEmpty():
            self._paint_selection(p)

        p.end()

    def _paint_grid(self, p: QPainter, W: int, H: int) -> None:
        pen = QPen(QColor(180, 180, 180, 160), 0)
        p.setPen(pen)
        scale = self._zoom / 100.0
        x = 0.0
        while x <= W:
            p.drawLine(int(x), 0, int(x), H)
            x += scale
        y = 0.0
        while y <= H:
            p.drawLine(0, int(y), W, int(y))
            y += scale

    def _paint_selection(self, p: QPainter) -> None:
        scale = self._zoom / 100.0
        r = self._selection
        sx = int(r.x() * scale)
        sy = int(r.y() * scale)
        sw = int(r.width() * scale)
        sh = int(r.height() * scale)

        pen = QPen(QColor(0, 0, 0), 1, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 4])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(sx, sy, sw, sh)

        pen2 = QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine)
        pen2.setDashPattern([4, 4])
        pen2.setDashOffset(4)
        p.setPen(pen2)
        p.drawRect(sx, sy, sw, sh)

    # ═══════════════════════════════════════════════════════════════════════
    # Mouse events
    # ═══════════════════════════════════════════════════════════════════════

    def mousePressEvent(self, event) -> None:
        if not self._tool:
            return
        btn = 1 if event.button() == Qt.MouseButton.LeftButton else 2
        self._button_held = btn
        x, y = self.screen_to_image(event.position().x(), event.position().y())
        self._tool.set_colors(self._fg, self._bg)
        if self._tool.on_press(self, x, y, btn):
            self.update()

    def mouseMoveEvent(self, event) -> None:
        x, y = self.screen_to_image(event.position().x(), event.position().y())
        self.mouse_moved.emit(x, y)
        if self._tool and self._button_held:
            self._tool.set_colors(self._fg, self._bg)
            if self._tool.on_move(self, x, y, self._button_held):
                self.update()

    def mouseReleaseEvent(self, event) -> None:
        if not self._tool:
            return
        x, y = self.screen_to_image(event.position().x(), event.position().y())
        if self._tool.on_release(self, x, y, self._button_held):
            self.update()
        self._button_held = 0

    # ═══════════════════════════════════════════════════════════════════════
    # Keyboard events
    # ═══════════════════════════════════════════════════════════════════════

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Shift:
            self.shift_held = True
        if event.key() == Qt.Key.Key_Escape:
            self._selection = None
            self.update()
        if self._tool:
            self._tool.on_key_press(event.key())

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Shift:
            self.shift_held = False
