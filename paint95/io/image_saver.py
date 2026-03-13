"""
Image saver — writes PNG or JPEG using Pillow.
"""
from pathlib import Path
from PIL import Image as PilImage
from PyQt6.QtGui import QImage

SUPPORTED_WRITE = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}


def save_image(image: QImage, path: str | Path, quality: int = 95) -> None:
    """Save a QImage as PNG or JPEG. Raises ValueError for other extensions."""
    p = Path(path)
    ext = p.suffix.lower()
    fmt = SUPPORTED_WRITE.get(ext)
    if fmt is None:
        raise ValueError(f"Extension non supportée : {ext}. Utilisez .png ou .jpg")

    # Convert to RGB888 for Pillow
    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = rgb.width(), rgb.height()
    ptr = rgb.constBits()
    ptr.setsize(height * width * 3)
    pil_img = PilImage.frombytes("RGB", (width, height), bytes(ptr))

    kwargs = {}
    if fmt == "JPEG":
        kwargs["quality"] = quality
        kwargs["optimize"] = True

    pil_img.save(str(p), fmt, **kwargs)
