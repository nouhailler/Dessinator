"""Load PNG / JPEG files into a QImage (ARGB32)."""
from pathlib import Path
from PyQt6.QtGui import QImage, QColor

SUPPORTED_READ = {".png", ".jpg", ".jpeg"}


class ImageLoader:
    @staticmethod
    def load(path: str) -> QImage:
        suffix = Path(path).suffix.lower()
        if suffix not in SUPPORTED_READ:
            raise ValueError(f"Format non supporté en lecture : {suffix}")
        image = QImage(path)
        if image.isNull():
            raise IOError(f"Impossible de charger l'image : {path}")
        return image.convertToFormat(QImage.Format.Format_ARGB32)

    @staticmethod
    def new_image(
        width: int = 800, height: int = 600, bg: str = "#ffffff"
    ) -> QImage:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor(bg))
        return image
