"""Flood-fill tool (scanline algorithm via Pillow for performance)."""
from __future__ import annotations
import io as _io
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtCore import QBuffer, QIODeviceBase
from PIL import Image, ImageDraw
from .base_tool import BaseTool


def _qimage_to_pil(image: QImage) -> Image.Image:
    buf = QBuffer()
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    image.save(buf, "PNG")
    buf.close()
    return Image.open(_io.BytesIO(bytes(buf.data()))).convert("RGBA")


def _pil_to_qimage(pil_img: Image.Image) -> QImage:
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height,
                  QImage.Format.Format_RGBA8888)
    return qimg.convertToFormat(QImage.Format.Format_ARGB32).copy()


class FillTool(BaseTool):
    name = "Remplissage"

    def on_press(self, canvas, x: int, y: int, button: int) -> bool:
        color = self._fg if button == 1 else self._bg
        new_image = self._flood_fill(canvas.image, x, y, color)
        if new_image is not None:
            canvas.save_undo()
            canvas.replace_image(new_image)
            return True
        return False

    def _flood_fill(self, image: QImage, x: int, y: int,
                    fill_color: QColor) -> QImage | None:
        w, h = image.width(), image.height()
        if not (0 <= x < w and 0 <= y < h):
            return None

        pil_img = _qimage_to_pil(image)
        target = pil_img.getpixel((x, y))
        fill = (fill_color.red(), fill_color.green(),
                fill_color.blue(), fill_color.alpha())

        if target == fill:
            return None

        ImageDraw.floodfill(pil_img, (x, y), fill, thresh=0)
        return _pil_to_qimage(pil_img)
