"""
Palette manager: default 28-color Paint-style palette + custom palette I/O.
"""
import json
from pathlib import Path
from PyQt6.QtGui import QColor


# Classic Paint 95 palette — 28 colours (14 × 2)
DEFAULT_PALETTE: list[str] = [
    "#000000", "#808080", "#800000", "#808000",
    "#008000", "#008080", "#000080", "#800080",
    "#808040", "#004040", "#0080FF", "#004080",
    "#8000FF", "#804000",
    "#FFFFFF", "#C0C0C0", "#FF0000", "#FFFF00",
    "#00FF00", "#00FFFF", "#0000FF", "#FF00FF",
    "#FFFF80", "#00FF80", "#80FFFF", "#8080FF",
    "#FF0080", "#FF8040",
]


class PaletteManager:
    """Holds the active colour palette and the two active colours."""

    def __init__(self) -> None:
        self._colors: list[QColor] = [QColor(c) for c in DEFAULT_PALETTE]
        self.foreground = QColor("#000000")
        self.background = QColor("#FFFFFF")

    # ------------------------------------------------------------------
    # Colour access
    # ------------------------------------------------------------------
    @property
    def colors(self) -> list[QColor]:
        return list(self._colors)

    def set_color(self, index: int, color: QColor) -> None:
        if 0 <= index < len(self._colors):
            self._colors[index] = color

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, path: Path) -> None:
        data = {
            "colors": [c.name() for c in self._colors],
            "foreground": self.foreground.name(),
            "background": self.background.name(),
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self._colors = [QColor(c) for c in data.get("colors", DEFAULT_PALETTE)]
        self.foreground = QColor(data.get("foreground", "#000000"))
        self.background = QColor(data.get("background", "#FFFFFF"))
