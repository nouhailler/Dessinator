#!/usr/bin/env python3
"""Dessinator — outil de dessin type Paint, moderne, sous Linux.

Lancement :
    python main.py
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path regardless of cwd
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Dessinator")
    app.setApplicationDisplayName("Dessinator")
    app.setApplicationVersion("1.0")
    # High-DPI support (Qt6 enables it by default, but be explicit)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    window = MainWindow()
    window.show()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            from file_io.image_loader import ImageLoader
            image = ImageLoader.load(path)
            window._canvas.load_image(image)
            window._current_path = path
            window._update_title()
            window._update_size_label()
        except Exception as e:
            print(f"Avertissement : impossible de charger {path} : {e}",
                  file=sys.stderr)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
