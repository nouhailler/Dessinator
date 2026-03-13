"""Circular undo/redo stack limited to 3 history levels."""
from collections import deque
from PyQt6.QtGui import QImage


class UndoManager:
    """Stores image snapshots for undo/redo. Max 3 undo levels."""

    def __init__(self, max_levels: int = 3):
        self._history: deque[QImage] = deque(maxlen=max_levels)
        self._redo: deque[QImage] = deque(maxlen=max_levels)

    def push(self, image: QImage) -> None:
        """Save current state before a modification."""
        self._history.append(image.copy())
        self._redo.clear()

    def undo(self, current_image: QImage) -> QImage | None:
        """Undo last action. Returns restored image, or None if nothing to undo."""
        if not self._history:
            return None
        self._redo.append(current_image.copy())
        return self._history.pop().copy()

    def redo(self, current_image: QImage) -> QImage | None:
        """Redo last undone action. Returns restored image, or None if nothing to redo."""
        if not self._redo:
            return None
        self._history.append(current_image.copy())
        return self._redo.pop().copy()

    def can_undo(self) -> bool:
        return len(self._history) > 0

    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def clear(self) -> None:
        self._history.clear()
        self._redo.clear()
