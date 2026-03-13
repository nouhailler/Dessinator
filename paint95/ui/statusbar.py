"""
Status bar: cursor position, image size, active tool.
"""
from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt


class StatusBar(QStatusBar):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pos_label = QLabel("x=0, y=0")
        self._size_label = QLabel("800 × 600")
        self._tool_label = QLabel("Crayon")
        self._zoom_label = QLabel("100%")

        self.addWidget(self._pos_label)
        self.addPermanentWidget(self._tool_label)
        self.addPermanentWidget(self._zoom_label)
        self.addPermanentWidget(self._size_label)

    def update_cursor(self, x: int, y: int) -> None:
        self._pos_label.setText(f"x={x}, y={y}")

    def update_size(self, w: int, h: int) -> None:
        self._size_label.setText(f"{w} × {h}")

    def update_tool(self, name: str) -> None:
        names = {
            "pencil": "Crayon",
            "brush": "Pinceau",
            "eraser": "Gomme",
            "spray": "Aérographe",
            "fill": "Remplissage",
            "pipette": "Pipette",
            "line": "Ligne",
            "rectangle": "Rectangle",
            "ellipse": "Ellipse",
            "polygon": "Polygone",
            "curve": "Courbe",
            "text": "Texte",
            "select_rect": "Sélection rect.",
            "select_free": "Sélection libre",
        }
        self._tool_label.setText(names.get(name, name))

    def update_zoom(self, zoom: float) -> None:
        self._zoom_label.setText(f"{round(zoom * 100)}%")
