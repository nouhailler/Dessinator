"""
Image loader — reads PNG and JPEG files via Pillow, returns a QImage.
"""
from pathlib import Path
from PIL import Image as PilImage
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QSize

SUPPORTED_READ = ["PNG", "JPEG", "JPG"]


def load_image(path: str | Path) -> QImage:
    """Load a PNG or JPEG file and return a QImage (Format_RGB32)."""
    p = Path(path)
    suffix = p.suffix.lstrip(".").upper()
    if suffix == "JPG":
        suffix = "JPEG"
    if suffix not in SUPPORTED_READ:
        raise ValueError(f"Format non supporté : {suffix}")

    pil_img = PilImage.open(p).convert("RGB")
    data = pil_img.tobytes("raw", "RGB")
    qimg = QImage(data, pil_img.width, pil_img.height,
                  pil_img.width * 3, QImage.Format.Format_RGB888)
    return qimg.convertToFormat(QImage.Format.Format_RGB32).copy()
