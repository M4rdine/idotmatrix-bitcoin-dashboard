"""Pixel-perfect 3x5 bitmap font for 16x16 LED displays.

Each character is a 3-wide x 5-tall grid of pixels.
Designed for maximum legibility at the smallest possible size.
1 pixel spacing between characters, 1 pixel spacing between lines.
"""

from __future__ import annotations

from PIL import Image

# Each glyph is a list of 5 rows, each row is a tuple of active pixel columns (0-indexed)
# Character width is 3px, height is 5px
GLYPHS: dict[str, list[tuple[int, ...]]] = {
    "0": [(0, 1, 2), (0, 2), (0, 2), (0, 2), (0, 1, 2)],
    "1": [(1,), (0, 1), (1,), (1,), (0, 1, 2)],
    "2": [(0, 1, 2), (2,), (0, 1, 2), (0,), (0, 1, 2)],
    "3": [(0, 1, 2), (2,), (0, 1, 2), (2,), (0, 1, 2)],
    "4": [(0, 2), (0, 2), (0, 1, 2), (2,), (2,)],
    "5": [(0, 1, 2), (0,), (0, 1, 2), (2,), (0, 1, 2)],
    "6": [(0, 1, 2), (0,), (0, 1, 2), (0, 2), (0, 1, 2)],
    "7": [(0, 1, 2), (2,), (2,), (2,), (2,)],
    "8": [(0, 1, 2), (0, 2), (0, 1, 2), (0, 2), (0, 1, 2)],
    "9": [(0, 1, 2), (0, 2), (0, 1, 2), (2,), (0, 1, 2)],
    "$": [(0, 1, 2), (0, 1), (0, 1, 2), (1, 2), (0, 1, 2)],
    ",": [(), (), (), (1,), (0,)],
    ".": [(), (), (), (), (0,)],
    "-": [(), (), (0, 1, 2), (), ()],
    "+": [(), (1,), (0, 1, 2), (1,), ()],
    "%": [(0, 2), (2,), (1,), (0,), (0, 2)],
    " ": [(), (), (), (), ()],
    "k": [(0, 2), (0, 1), (0, 1), (0, 1), (0, 2)],
    "B": [(0, 1), (0, 2), (0, 1), (0, 2), (0, 1)],
    "T": [(0, 1, 2), (1,), (1,), (1,), (1,)],
    "C": [(0, 1, 2), (0,), (0,), (0,), (0, 1, 2)],
    "U": [(0, 2), (0, 2), (0, 2), (0, 2), (0, 1, 2)],
    "S": [(0, 1, 2), (0,), (0, 1, 2), (2,), (0, 1, 2)],
    "D": [(0, 1), (0, 2), (0, 2), (0, 2), (0, 1)],
}

CHAR_WIDTH = 3
CHAR_HEIGHT = 5
CHAR_SPACING = 1


def measure_text(text: str) -> int:
    """Return the pixel width of a text string."""
    if not text:
        return 0
    width = 0
    for i, ch in enumerate(text):
        glyph = GLYPHS.get(ch)
        if glyph is None:
            glyph = GLYPHS.get(" ")
        char_w = _glyph_width(ch)
        width += char_w
        if i < len(text) - 1:
            width += CHAR_SPACING
    return width


def _glyph_width(ch: str) -> int:
    """Get the effective width of a character."""
    if ch == " ":
        return 2
    if ch in (",", "."):
        return 2
    return CHAR_WIDTH


def draw_text(
    img: Image.Image,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> int:
    """Draw pixel-perfect text onto an image.

    Returns the x position after the last character (for chaining).
    """
    cursor_x = x
    for ch in text:
        glyph = GLYPHS.get(ch)
        if glyph is None:
            glyph = GLYPHS.get(" ", [(), (), (), (), ()])
        char_w = _glyph_width(ch)

        for row_idx, row_pixels in enumerate(glyph):
            py = y + row_idx
            if py < 0 or py >= img.height:
                continue
            for px_offset in row_pixels:
                px = cursor_x + px_offset
                if 0 <= px < img.width:
                    img.putpixel((px, py), color)

        cursor_x += char_w + CHAR_SPACING

    return cursor_x


# Bitcoin ₿ icon - 5x7 pixels, hand-crafted
BTC_ICON_PIXELS: list[tuple[int, int]] = [
    # Vertical lines through
    (2, 0), (2, 8),
    # Left vertical bar
    (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),
    (1, 1), (1, 7),
    # Top curve
    (1, 1), (2, 1), (3, 1),
    (3, 2), (4, 2),
    # Middle
    (1, 4), (2, 4), (3, 4),
    (3, 3), (4, 3),
    # Bottom curve
    (1, 7), (2, 7), (3, 7),
    (3, 5), (4, 5),
    (3, 6), (4, 6),
]


def draw_btc_icon(
    img: Image.Image,
    x: int,
    y: int,
    color: tuple[int, int, int] = (247, 147, 26),
) -> None:
    """Draw a 5x9 pixel Bitcoin ₿ symbol."""
    for px, py in BTC_ICON_PIXELS:
        ix = x + px
        iy = y + py
        if 0 <= ix < img.width and 0 <= iy < img.height:
            img.putpixel((ix, iy), color)
