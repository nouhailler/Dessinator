"""
Entry point for Dessinator — modern Paint-like drawing tool.
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Dessinator")
    app.setOrganizationName("Dessinator")

    # High-DPI support
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
