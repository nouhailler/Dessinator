"""Color palette management — 28-colour Paint-inspired palette."""
import json
from pathlib import Path
from PyQt6.QtGui import QColor

# Classic Paint-inspired 28-colour palette (14 columns × 2 rows)
DEFAULT_PALETTE: list[str] = [
    # Row 1 — darker tones
    "#000000", "#7f7f7f", "#880015", "#ed1c24",
    "#ff7f27", "#fff200", "#22b14c", "#00a2e8",
    "#3f48cc", "#a349a4", "#ffffff", "#c3c3c3",
    "#b97a57", "#ffaec9",
    # Row 2 — lighter / vivid tones
    "#ff0000", "#ff6600", "#ffff00", "#00ff00",
    "#00ffff", "#0000ff", "#8000ff", "#ff00ff",
    "#804000", "#ff8080", "#80ff80", "#8080ff",
    "#ff80ff", "#80ffff",
]


class PaletteManager:
    def __init__(self) -> None:
        self._colors: list[QColor] = [QColor(c) for c in DEFAULT_PALETTE]
        self._foreground: QColor = QColor("#000000")
        self._background: QColor = QColor("#ffffff")

    # ── colours ────────────────────────────────────────────────────────────
    @property
    def colors(self) -> list[QColor]:
        return self._colors

    # ── foreground / background ─────────────────────────────────────────────
    @property
    def foreground(self) -> QColor:
        return self._foreground

    @foreground.setter
    def foreground(self, color: QColor) -> None:
        self._foreground = color

    @property
    def background(self) -> QColor:
        return self._background

    @background.setter
    def background(self, color: QColor) -> None:
        self._background = color

    # ── persistence ─────────────────────────────────────────────────────────
    def save(self, path: str) -> None:
        data = {
            "colors": [c.name() for c in self._colors],
            "foreground": self._foreground.name(),
            "background": self._background.name(),
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: str) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._colors = [QColor(c) for c in data.get("colors", DEFAULT_PALETTE)]
        self._foreground = QColor(data.get("foreground", "#000000"))
        self._background = QColor(data.get("background", "#ffffff"))
