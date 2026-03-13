"""Text tool — rasterised text insertion with font dialog."""
from __future__ import annotations
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFontDialog,
                              QDialogButtonBox)
from .base_tool import BaseTool


class TextDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Insérer du texte")
        self._font = QFont("Sans Serif", 14)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Texte :"))
        self._text_edit = QLineEdit()
        layout.addWidget(self._text_edit)

        row = QHBoxLayout()
        self._font_label = QLabel(self._describe_font())
        self._font_btn = QPushButton("Police…")
        self._font_btn.clicked.connect(self._pick_font)
        row.addWidget(self._font_label, stretch=1)
        row.addWidget(self._font_btn)
        layout.addLayout(row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick_font(self) -> None:
        ok, font = QFontDialog.getFont(self._font, self)
        if ok:
            self._font = font
            self._font_label.setText(self._describe_font())

    def _describe_font(self) -> str:
        style = ""
        if self._font.bold():
            style += "Gras "
        if self._font.italic():
            style += "Italique "
        return f"{self._font.family()}, {self._font.pointSize()}pt {style}".strip()

    def set_font(self, font: QFont) -> None:
        self._font = font
        self._font_label.setText(self._describe_font())

    def text(self) -> str:
        return self._text_edit.text()

    def font(self) -> QFont:
        return self._font


class TextTool(BaseTool):
    name = "Texte"

    def __init__(self) -> None:
        super().__init__()
        self._font = QFont("Sans Serif", 14)

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        dlg = TextDialog(canvas.parent())
        dlg.set_font(self._font)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            text = dlg.text()
            self._font = dlg.font()
            if text:
                canvas.save_undo()
                painter = QPainter(canvas.image)
                painter.setPen(self._fg if button == 1 else self._bg)
                painter.setFont(self._font)
                painter.drawText(x, y, text)
                painter.end()
                return True
        return False
