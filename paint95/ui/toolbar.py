"""Left-side toolbox + options panel.

The toolbox shows all tools as icon buttons in a 2-column grid.
Below the grid a small options area displays controls relevant
to the active tool (size, shape, fill mode, thickness, …).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QButtonGroup, QGroupBox, QSizePolicy,
)

from tools.pencil import PencilTool
from tools.brush import BrushTool, SIZES as BRUSH_SIZES, SHAPES as BRUSH_SHAPES
from tools.eraser import EraserTool, SIZES as ERASER_SIZES
from tools.spray import SprayTool
from tools.fill import FillTool
from tools.pipette import PipetteTool
from tools.text_tool import TextTool
from tools.selection_tool import SelectionTool
from tools.shapes import LineTool, RectangleTool, EllipseTool, PolygonTool, FillMode


# ── tool descriptors ─────────────────────────────────────────────────────────

_TOOL_DEFS = [
    ("✏",   "Crayon",      "pencil"),
    ("🖌",   "Pinceau",     "brush"),
    ("⌫",   "Gomme",       "eraser"),
    ("✦",   "Aérographe",  "spray"),
    ("▣",   "Remplissage", "fill"),
    ("⊕",   "Pipette",     "pipette"),
    ("A",   "Texte",       "text"),
    ("⬚",   "Sélection",   "selection"),
    ("/",   "Ligne",       "line"),
    ("▭",   "Rectangle",   "rectangle"),
    ("○",   "Ellipse",     "ellipse"),
    ("⬡",   "Polygone",    "polygon"),
]


class ToolButton(QPushButton):
    def __init__(self, icon_text: str, tooltip: str) -> None:
        super().__init__(icon_text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(36, 36)
        font = self.font()
        font.setPointSize(14)
        self.setFont(font)
        self.setStyleSheet("""
            QPushButton { border: 1px solid #aaa; background: #e8e8e8; }
            QPushButton:hover { background: #d0d0f0; }
            QPushButton:checked { background: #a0a8e0; border: 2px inset #666; }
        """)


class OptionsPanel(QGroupBox):
    """Dynamically shows controls for the active tool."""

    def __init__(self, parent=None) -> None:
        super().__init__("Options", parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 8, 4, 4)
        self._layout.setSpacing(4)
        self.setMinimumWidth(80)

    def clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── per-tool option builders ─────────────────────────────────────────────

    def for_brush(self, tool: BrushTool) -> None:
        self.clear()
        self._layout.addWidget(QLabel("Taille :"))
        cb = QComboBox()
        for s in BRUSH_SIZES:
            cb.addItem(f"{s} px", s)
        cb.setCurrentIndex(BRUSH_SIZES.index(tool.size))
        cb.currentIndexChanged.connect(
            lambda i: setattr(tool, "size", BRUSH_SIZES[i]))
        self._layout.addWidget(cb)

        self._layout.addWidget(QLabel("Forme :"))
        cb2 = QComboBox()
        cb2.addItems(["Rond", "Carré"])
        cb2.setCurrentIndex(BRUSH_SHAPES.index(tool.shape))
        cb2.currentIndexChanged.connect(
            lambda i: setattr(tool, "shape", BRUSH_SHAPES[i]))
        self._layout.addWidget(cb2)
        self._layout.addStretch()

    def for_eraser(self, tool: EraserTool) -> None:
        self.clear()
        self._layout.addWidget(QLabel("Taille :"))
        cb = QComboBox()
        for s in ERASER_SIZES:
            cb.addItem(f"{s} px", s)
        cb.setCurrentIndex(ERASER_SIZES.index(tool.size))
        cb.currentIndexChanged.connect(
            lambda i: setattr(tool, "size", ERASER_SIZES[i]))
        self._layout.addWidget(cb)
        self._layout.addStretch()

    def for_spray(self, tool: SprayTool) -> None:
        self.clear()
        self._layout.addWidget(QLabel("Rayon :"))
        sb = QSpinBox()
        sb.setRange(5, 50)
        sb.setValue(tool.radius)
        sb.valueChanged.connect(lambda v: setattr(tool, "radius", v))
        self._layout.addWidget(sb)

        self._layout.addWidget(QLabel("Densité :"))
        sb2 = QSpinBox()
        sb2.setRange(1, 100)
        sb2.setValue(tool.density)
        sb2.valueChanged.connect(lambda v: setattr(tool, "density", v))
        self._layout.addWidget(sb2)
        self._layout.addStretch()

    def for_shape(self, tool) -> None:
        """Shared options for Line / Rectangle / Ellipse / Polygon."""
        self.clear()
        self._layout.addWidget(QLabel("Épaisseur :"))
        sb = QSpinBox()
        sb.setRange(1, 20)
        sb.setValue(getattr(tool, "thickness", 1))
        sb.valueChanged.connect(lambda v: setattr(tool, "thickness", v))
        self._layout.addWidget(sb)

        if hasattr(tool, "fill_mode"):
            self._layout.addWidget(QLabel("Remplissage :"))
            cb = QComboBox()
            cb.addItem("Contour", FillMode.OUTLINE)
            cb.addItem("Rempli", FillMode.FILLED)
            cb.addItem("Les deux", FillMode.BOTH)
            modes = [FillMode.OUTLINE, FillMode.FILLED, FillMode.BOTH]
            cb.setCurrentIndex(modes.index(tool.fill_mode))
            cb.currentIndexChanged.connect(
                lambda i: setattr(tool, "fill_mode", modes[i]))
            self._layout.addWidget(cb)

        self._layout.addStretch()

    def for_generic(self) -> None:
        self.clear()
        self._layout.addStretch()


class ToolBox(QWidget):
    """Left panel: tool buttons + options."""

    tool_selected = pyqtSignal(object)   # emits the tool instance

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(84)

        # ── instantiate all tools ────────────────────────────────────────────
        self._pencil = PencilTool()
        self._brush = BrushTool()
        self._eraser = EraserTool()
        self._spray = SprayTool()
        self._fill = FillTool()
        self._pipette = PipetteTool()
        self._text = TextTool()
        self._selection = SelectionTool()
        self._line = LineTool()
        self._rectangle = RectangleTool()
        self._ellipse = EllipseTool()
        self._polygon = PolygonTool()

        self._tool_map = {
            "pencil":    self._pencil,
            "brush":     self._brush,
            "eraser":    self._eraser,
            "spray":     self._spray,
            "fill":      self._fill,
            "pipette":   self._pipette,
            "text":      self._text,
            "selection": self._selection,
            "line":      self._line,
            "rectangle": self._rectangle,
            "ellipse":   self._ellipse,
            "polygon":   self._polygon,
        }

        self._build_ui()
        # Select pencil by default
        self._buttons["pencil"].setChecked(True)
        self._activate("pencil")

    # ── public helpers ───────────────────────────────────────────────────────

    def set_pipette_callbacks(self, fg_cb, bg_cb) -> None:
        self._pipette.set_callbacks(fg_cb, bg_cb)

    def tool(self, key: str):
        return self._tool_map.get(key)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        outer.setSpacing(4)

        grid = QGridLayout()
        grid.setSpacing(2)

        self._buttons: dict[str, ToolButton] = {}
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        for idx, (icon, tip, key) in enumerate(_TOOL_DEFS):
            btn = ToolButton(icon, tip)
            self._buttons[key] = btn
            self._btn_group.addButton(btn)
            row, col = divmod(idx, 2)
            grid.addWidget(btn, row, col)
            btn.clicked.connect(lambda checked, k=key: self._activate(k))

        outer.addLayout(grid)

        self._options = OptionsPanel()
        outer.addWidget(self._options)

    def _activate(self, key: str) -> None:
        tool = self._tool_map[key]

        # Update options panel
        if key == "brush":
            self._options.for_brush(self._brush)
        elif key == "eraser":
            self._options.for_eraser(self._eraser)
        elif key == "spray":
            self._options.for_spray(self._spray)
        elif key in ("line", "rectangle", "ellipse", "polygon"):
            self._options.for_shape(tool)
        else:
            self._options.for_generic()

        self.tool_selected.emit(tool)
