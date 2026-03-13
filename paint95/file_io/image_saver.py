"""Save a QImage to PNG or JPEG via Pillow."""
import io as _io
from pathlib import Path
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer, QIODeviceBase
from PIL import Image

SUPPORTED_WRITE = {".png", ".jpg", ".jpeg"}


def _qimage_to_pil(image: QImage) -> Image.Image:
    """Convert QImage (any format) → PIL RGBA Image."""
    buf = QBuffer()
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    image.save(buf, "PNG")
    buf.close()
    return Image.open(_io.BytesIO(bytes(buf.data()))).convert("RGBA")


class ImageSaver:
    @staticmethod
    def save(image: QImage, path: str, jpeg_quality: int = 92) -> None:
        suffix = Path(path).suffix.lower()
        if suffix not in SUPPORTED_WRITE:
            raise ValueError(f"Format non supporté en écriture : {suffix}")

        pil_img = _qimage_to_pil(image)

        if suffix in {".jpg", ".jpeg"}:
            pil_img = pil_img.convert("RGB")
            pil_img.save(path, "JPEG", quality=jpeg_quality, optimize=True)
        else:
            pil_img.save(path, "PNG", optimize=True)
