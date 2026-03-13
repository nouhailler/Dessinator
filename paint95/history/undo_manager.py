"""
Undo/Redo manager using a circular stack of image snapshots.
Limited to 3 levels of undo as per specifications.
"""
from collections import deque
from PyQt6.QtGui import QImage


MAX_UNDO_LEVELS = 3


class UndoManager:
    """Manages undo/redo history with image snapshots."""

    def __init__(self, max_levels: int = MAX_UNDO_LEVELS):
        self._max_levels = max_levels
        self._undo_stack: deque[QImage] = deque(maxlen=max_levels)
        self._redo_stack: deque[QImage] = deque(maxlen=max_levels)

    def save_state(self, image: QImage) -> None:
        """Save a snapshot of the current canvas state."""
        self._undo_stack.append(image.copy())
        self._redo_stack.clear()

    def undo(self, current_image: QImage) -> QImage | None:
        """Return the previous state, or None if unavailable."""
        if not self._undo_stack:
            return None
        self._redo_stack.append(current_image.copy())
        return self._undo_stack.pop()

    def redo(self, current_image: QImage) -> QImage | None:
        """Return the next (redone) state, or None if unavailable."""
        if not self._redo_stack:
            return None
        self._undo_stack.append(current_image.copy())
        return self._redo_stack.pop()

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
