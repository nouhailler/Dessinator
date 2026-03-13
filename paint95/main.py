"""
Entry point for Dessinator — modern Paint-like drawing tool.
"""
import sys
from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Dessinator")
    app.setOrganizationName("Dessinator")

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
