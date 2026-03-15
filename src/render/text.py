"""Text rendering utilities for low-resolution LED displays.

Uses Pillow to render text onto small bitmaps suitable for
16x16, 32x32, or 64x64 pixel displays. Includes a built-in
minimal pixel font for small sizes and uses system fonts when available.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.render.colors import COLORS, RGB


FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

_font_cache: dict[tuple[str | None, int], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def _get_font(
    size: int,
    font_path: str | None = None,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font, with caching.

    Tries in order:
    1. Custom font from font_path
    2. Pixel font from fonts/ directory
    3. Pillow default font
    """
    cache_key = (font_path, size)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont

    if font_path:
        try:
            font = ImageFont.truetype(font_path, size)
            _font_cache[cache_key] = font
            return font
        except OSError:
            pass

    pixel_font = FONTS_DIR / "pixel.ttf"
    if pixel_font.exists():
        try:
            font = ImageFont.truetype(str(pixel_font), size)
            _font_cache[cache_key] = font
            return font
        except OSError:
            pass

    font = ImageFont.load_default()
    _font_cache[cache_key] = font
    return font


def render_text_line(
    text: str,
    width: int,
    height: int,
    color: RGB = COLORS.WHITE,
    bg_color: RGB = COLORS.BLACK,
    font_size: int = 8,
    font_path: str | None = None,
    align: str = "left",
    y_offset: int = 0,
) -> Image.Image:
    """Render a single line of text onto a Pillow Image.

    Args:
        text: The text to render.
        width: Image width in pixels.
        height: Image height in pixels.
        color: Text color.
        bg_color: Background color.
        font_size: Font size in points.
        font_path: Optional path to a .ttf font file.
        align: Text alignment - "left", "center", or "right".
        y_offset: Vertical offset from top.

    Returns:
        A Pillow Image with the rendered text.
    """
    image = Image.new("RGB", (width, height), bg_color.tuple)
    draw = ImageDraw.Draw(image)
    font = _get_font(font_size, font_path)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    if align == "center":
        x = max(0, (width - text_width) // 2)
    elif align == "right":
        x = max(0, width - text_width - 1)
    else:
        x = 1

    y = y_offset if y_offset else max(0, (height - text_height) // 2)

    draw.text((x, y), text, fill=color.tuple, font=font)
    return image


def render_multiline(
    lines: list[tuple[str, RGB]],
    width: int,
    height: int,
    bg_color: RGB = COLORS.BLACK,
    font_size: int = 8,
    font_path: str | None = None,
    line_spacing: int = 2,
    start_y: int = 0,
) -> Image.Image:
    """Render multiple lines of text with individual colors.

    Args:
        lines: List of (text, color) tuples.
        width: Image width in pixels.
        height: Image height in pixels.
        bg_color: Background color.
        font_size: Font size in points.
        font_path: Optional path to a .ttf font file.
        line_spacing: Pixels between lines.
        start_y: Starting Y position.

    Returns:
        A Pillow Image with all lines rendered.
    """
    image = Image.new("RGB", (width, height), bg_color.tuple)
    draw = ImageDraw.Draw(image)
    font = _get_font(font_size, font_path)

    y = start_y
    for text, color in lines:
        if y >= height:
            break
        draw.text((1, y), text, fill=color.tuple, font=font)
        bbox = draw.textbbox((0, 0), text, font=font)
        line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing

    return image


def measure_text(
    text: str,
    font_size: int = 8,
    font_path: str | None = None,
) -> tuple[int, int]:
    """Measure the pixel dimensions of rendered text.

    Returns:
        (width, height) tuple.
    """
    font = _get_font(font_size, font_path)
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])
