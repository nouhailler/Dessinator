"""
Vertical tool palette — icon buttons for each drawing tool.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QButtonGroup,
    QLabel, QComboBox, QSpinBox, QFrame, QSizePolicy,
)
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal


def _make_icon(symbol: str, color: str = "#222222") -> QIcon:
    """Create a simple text/symbol icon on a transparent background."""
    px = QPixmap(28, 28)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setPen(QColor(color))
    font = QFont("Monospace", 14, QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
    p.end()
    return QIcon(px)


TOOL_DEFS = [
    ("pencil",       "✏",  "Crayon (P)"),
    ("brush",        "🖌",  "Pinceau (B)"),
    ("eraser",       "⬜",  "Gomme (E)"),
    ("spray",        "💨",  "Aérographe (A)"),
    ("fill",         "🪣",  "Remplissage (F)"),
    ("pipette",      "💉",  "Pipette (I)"),
    ("line",         "╱",  "Ligne (L)"),
    ("rectangle",    "▭",  "Rectangle (R)"),
    ("ellipse",      "⬭",  "Ellipse (O)"),
    ("polygon",      "⬠",  "Polygone (G)"),
    ("curve",        "〜",  "Courbe (U)"),
    ("text",         "T",  "Texte (X)"),
    ("select_rect",  "⬚",  "Sélection rect. (S)"),
    ("select_free",  "⌇",  "Sélection libre (W)"),
]

KEY_MAP = {
    "p": "pencil", "b": "brush", "e": "eraser", "a": "spray",
    "f": "fill",   "i": "pipette", "l": "line", "r": "rectangle",
    "o": "ellipse", "g": "polygon", "u": "curve", "x": "text",
    "s": "select_rect", "w": "select_free",
}


class ToolBar(QWidget):
    """Vertical toolbar with tool buttons."""

    tool_selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(48)
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(2)

        self._buttons: dict[str, QToolButton] = {}

        for name, symbol, tooltip in TOOL_DEFS:
            btn = QToolButton()
            btn.setCheckable(True)
            btn.setIcon(_make_icon(symbol))
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(tooltip)
            btn.setFixedSize(42, 36)
            btn.clicked.connect(lambda checked, n=name: self.tool_selected.emit(n))
            self._btn_group.addButton(btn)
            self._buttons[name] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Select pencil by default
        self._buttons["pencil"].setChecked(True)

    def select_tool(self, name: str) -> None:
        btn = self._buttons.get(name)
        if btn:
            btn.setChecked(True)
