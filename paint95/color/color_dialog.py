"""
Extended colour picker that shows both RGB and HSV sliders,
plus a button to replace a palette slot.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QSpinBox, QPushButton, QColorDialog,
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal


class ColorPickerDialog(QDialog):
    """
    Thin wrapper around Qt's native QColorDialog so the caller
    always gets a QColor back via the standard exec() pattern.
    """

    color_selected = pyqtSignal(QColor)

    def __init__(self, initial: QColor, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Choisir une couleur")
        self._color = initial

        layout = QVBoxLayout(self)

        self._dialog = QColorDialog(initial, self)
        self._dialog.setWindowFlags(Qt.WindowType.Widget)
        self._dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        layout.addWidget(self._dialog)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _accept(self) -> None:
        self._color = self._dialog.currentColor()
        self.color_selected.emit(self._color)
        self.accept()

    def selected_color(self) -> QColor:
        return self._color
