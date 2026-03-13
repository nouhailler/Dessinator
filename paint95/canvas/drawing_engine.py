"""
Drawing engine: owns the QImage buffer and dispatches events to the active tool.
"""
from PyQt6.QtGui import QImage, QColor, QPainter
from PyQt6.QtCore import QPoint, QSize, Qt, pyqtSignal, QObject

from ..history.undo_manager import UndoManager
from ..tools.base import BaseTool


class DrawingEngine(QObject):
    """Owns the canvas QImage and routes tool events."""

    image_changed = pyqtSignal()

    def __init__(self, width: int = 800, height: int = 600, parent=None) -> None:
        super().__init__(parent)
        self._undo = UndoManager()
        self._image = self._blank(width, height)
        self._tool: BaseTool | None = None

    # ------------------------------------------------------------------
    # Image access
    # ------------------------------------------------------------------
    @property
    def image(self) -> QImage:
        return self._image

    def resize(self, width: int, height: int) -> None:
        new_img = self._blank(width, height)
        p = QPainter(new_img)
        p.drawImage(QPoint(0, 0), self._image)
        p.end()
        self._image = new_img
        self._undo.clear()
        self.image_changed.emit()

    def replace_image(self, img: QImage) -> None:
        self._image = img.convertToFormat(QImage.Format.Format_RGB32)
        self._undo.clear()
        self.image_changed.emit()

    @staticmethod
    def _blank(w: int, h: int) -> QImage:
        img = QImage(w, h, QImage.Format.Format_RGB32)
        img.fill(QColor("#FFFFFF"))
        return img

    def new(self, width: int, height: int) -> None:
        self._undo.save_state(self._image)
        self._image = self._blank(width, height)
        self._undo.clear()
        self.image_changed.emit()

    # ------------------------------------------------------------------
    # Tool
    # ------------------------------------------------------------------
    def set_tool(self, tool: BaseTool) -> None:
        self._tool = tool

    # ------------------------------------------------------------------
    # Mouse events — called by CanvasWidget
    # ------------------------------------------------------------------
    def press(self, pos: QPoint, button: int) -> None:
        if self._tool is None:
            return
        self._undo.save_state(self._image)
        changed = self._tool.on_press(self._image, pos, button)
        if changed:
            self.image_changed.emit()

    def move(self, pos: QPoint, button: int) -> None:
        if self._tool is None:
            return
        changed = self._tool.on_move(self._image, pos, button)
        if changed:
            self.image_changed.emit()

    def release(self, pos: QPoint, button: int) -> None:
        if self._tool is None:
            return
        changed = self._tool.on_release(self._image, pos, button)
        if changed:
            self.image_changed.emit()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------
    def undo(self) -> None:
        result = self._undo.undo(self._image)
        if result is not None:
            self._image = result
            self.image_changed.emit()

    def redo(self) -> None:
        result = self._undo.redo(self._image)
        if result is not None:
            self._image = result
            self.image_changed.emit()

    def can_undo(self) -> bool:
        return self._undo.can_undo()

    def can_redo(self) -> bool:
        return self._undo.can_redo()

    def save_state(self) -> None:
        self._undo.save_state(self._image)

    # ------------------------------------------------------------------
    # Image operations
    # ------------------------------------------------------------------
    def invert_colors(self) -> None:
        self._undo.save_state(self._image)
        self._image.invertPixels()
        self.image_changed.emit()

    def flip_horizontal(self) -> None:
        self._undo.save_state(self._image)
        self._image = self._image.mirrored(horizontal=True, vertical=False)
        self.image_changed.emit()

    def flip_vertical(self) -> None:
        self._undo.save_state(self._image)
        self._image = self._image.mirrored(horizontal=False, vertical=True)
        self.image_changed.emit()
