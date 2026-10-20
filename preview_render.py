"""Shared rendering of the 1bpp card preview bitmaps.

A card slot stores its 1bpp preview bitmaps next to the stitch data
(``preview_raw``).  The field holds the main preview followed by one block per
additional thread colour (Embroidery only); ``decode_card_preview`` renders the
first block, while ``split_preview_blocks`` exposes all of them.

Both the Memory Card tab (48 px slot tiles) and the card slot detail window (a
much larger preview) need to draw these, so the decoding and the scalable widget
live here instead of being duplicated in each tab.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap, QTransform
from PyQt5.QtWidgets import QWidget

# The bitmap is stored column-major: each column is ``col_height / 8``
# consecutive bytes, one bit per pixel.
COL_HEIGHT_9MM = 24
COL_HEIGHT_DEFAULT = 48       # MAXI and Embroidery

# Size of one preview bitmap per pattern type, in bytes.
PREVIEW_SIZE_9MM = 159
PREVIEW_SIZE_MAXI = 318
PREVIEW_SIZE_EMBROIDERY = 288
PREVIEW_SIZES = {
    "9mm": PREVIEW_SIZE_9MM,
    "MAXI": PREVIEW_SIZE_MAXI,
    "Embroidery": PREVIEW_SIZE_EMBROIDERY,
}

# One preview-ish block per thread colour.  Kept as a named constant because the
# per-colour blocks are what used to be stored in the separate colours field.
COLOR_PREVIEW_BYTES = PREVIEW_SIZE_EMBROIDERY


def main_preview_raw(preview_raw: str, pattern_type: str) -> str:
    """Return only the first (main) preview block of ``preview_raw``.

    ``preview_raw`` holds all preview bitmaps concatenated: the main preview
    followed by one block per additional thread colour.  Callers that only want
    the main image (slot tiles, KB reads) use this helper.
    """
    block_bytes = PREVIEW_SIZES.get(pattern_type)
    if not preview_raw or not block_bytes:
        return preview_raw or ""
    return preview_raw[:block_bytes * 2]


def split_preview_blocks(preview_raw: str, block_bytes: int = COLOR_PREVIEW_BYTES):
    """Split the preview field into its fixed-size per-colour blocks.

    Each block is a 1bpp bitmap encoded exactly like the main preview.  A
    trailing partial block is ignored.
    """
    if not preview_raw:
        return []
    raw = preview_raw.strip()
    chunk_chars = block_bytes * 2
    return [raw[i:i + chunk_chars]
            for i in range(0, len(raw) - chunk_chars + 1, chunk_chars)]


def decode_card_preview(preview_raw: str, pattern_type: str, is_embroidery: bool = False):
    """Build a QImage from the raw preview bytes, or ``None`` when unavailable.

    ``preview_raw`` is the hex string stored on the slot.  The column height
    depends on the pattern type: 9mm designs use 24-pixel columns (3 bytes
    each), MAXI and Embroidery use 48-pixel columns (6 bytes each).

    Embroidery previews are stored rotated by 180 degrees, so they are turned
    back before display.
    """
    if not preview_raw:
        return None
    try:
        data = bytes.fromhex(main_preview_raw(preview_raw, pattern_type).strip())
    except (ValueError, AttributeError):
        return None

    col_height = COL_HEIGHT_9MM if pattern_type == "9mm" else COL_HEIGHT_DEFAULT
    bytes_per_col = col_height // 8
    if len(data) < bytes_per_col:
        return None

    num_cols = len(data) // bytes_per_col
    img = QImage(num_cols, col_height, QImage.Format_RGB32)
    img.fill(QColor(255, 255, 255).rgb())
    black = QColor(0, 0, 0).rgb()

    for col in range(num_cols):
        for byte_idx in range(bytes_per_col):
            byte_val = data[col * bytes_per_col + byte_idx]
            # byte_idx=0 is the bottom-most 8-pixel group; the last byte is the top group.
            y_base = col_height - 8 - byte_idx * 8
            for bit in range(8):
                # MSB (bit 7) is the topmost pixel of this 8-pixel segment.
                if (byte_val >> (7 - bit)) & 1:
                    img.setPixel(col, y_base + bit, black)

    if is_embroidery:
        img = img.transformed(QTransform().rotate(180))

    return img


class CardPreviewImage(QWidget):
    """Draws a card's preview bitmap scaled by a whole-number factor.

    Nearest-neighbour scaling (``Qt.FastTransformation``) is deliberate: it keeps
    the 1bpp pixels crisp instead of blurring them into grey.
    """

    def __init__(self, target_height: int = 160, parent=None):
        super().__init__(parent)
        self._target_height = target_height
        self._display = None
        self.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        self.set_preview("", "")

    def set_preview(self, preview_raw: str, pattern_type: str, is_embroidery: bool = False):
        """Load (or clear) the bitmap.  Safe to call with empty data."""
        image = decode_card_preview(preview_raw, pattern_type, is_embroidery)
        pixmap = QPixmap.fromImage(image) if image is not None else None
        self._rescale(pixmap)
        self.update()

    def has_preview(self) -> bool:
        """True when a bitmap is currently displayed."""
        return self._display is not None

    def _rescale(self, pixmap):
        if pixmap is None or pixmap.isNull():
            self._display = None
            self.setFixedSize(80, self._target_height)
            return
        height = pixmap.height()
        width = pixmap.width()
        scale = max(1, self._target_height // max(height, 1))
        self._display = pixmap.scaled(width * scale, height * scale,
                                      Qt.KeepAspectRatio, Qt.FastTransformation)
        # +2 for the 1px border on each side
        self.setFixedSize(self._display.width() + 2, self._display.height() + 2)

    def paintEvent(self, event):
        if self._display is None:
            return
        painter = QPainter(self)
        painter.drawPixmap(1, 1, self._display)
        painter.end()
