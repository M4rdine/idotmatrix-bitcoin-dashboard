"""iDotMatrix protocol command builders.

Based on the reverse-engineered protocol from:
- github.com/derkalle4/python3-idotmatrix-library
- github.com/8none1/idotmatrix

Key discovery: images are sent as PNG files, not raw RGB data.
"""

from __future__ import annotations

import io
import struct
from dataclasses import dataclass

from PIL import Image


WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"
READ_UUID = "0000fa03-0000-1000-8000-00805f9b34fb"

MAX_CHUNK_SIZE = 4096


@dataclass(frozen=True)
class Color:
    """RGB color representation."""

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for channel, value in [("r", self.r), ("g", self.g), ("b", self.b)]:
            if not 0 <= value <= 255:
                raise ValueError(f"Color channel {channel} must be 0-255, got {value}")

    def to_bytes(self) -> bytes:
        return bytes([self.r, self.g, self.b])


def build_power_command(*, on: bool) -> bytearray:
    """Power on: [05 00 07 01 01], Power off: [05 00 07 01 00]."""
    return bytearray([0x05, 0x00, 0x07, 0x01, int(on)])


def build_brightness_command(percent: int) -> bytearray:
    """Brightness: [05 00 04 80 percent]."""
    clamped = max(0, min(100, percent))
    return bytearray([0x05, 0x00, 0x04, 0x80, clamped])


def build_image_mode_command(*, enable: bool) -> bytearray:
    """Enter/exit image mode: [05 00 04 01 01/00]."""
    return bytearray([0x05, 0x00, 0x04, 0x01, int(enable)])


def build_fullscreen_color_command(r: int, g: int, b: int) -> bytearray:
    """Fullscreen color: [07 00 02 02 R G B]."""
    color = Color(r, g, b)
    return bytearray([0x07, 0x00, 0x02, 0x02]) + bytearray(color.to_bytes())


def build_pixel_command(x: int, y: int, r: int, g: int, b: int) -> bytearray:
    """Single pixel: [0A 00 05 01 00 R G B X Y]."""
    color = Color(r, g, b)
    return bytearray([0x0A, 0x00, 0x05, 0x01, 0x00]) + bytearray(
        color.to_bytes()
    ) + bytearray([x, y])


def build_reset_command() -> bytearray:
    """Reset device: [04 00 03 80]."""
    return bytearray([0x04, 0x00, 0x03, 0x80])


def pil_image_to_png_bytes(image: Image.Image, size: int) -> bytes:
    """Convert a Pillow Image to PNG bytes for the iDotMatrix protocol.

    The device expects a PNG file, not raw RGB data.
    """
    if image.size != (size, size):
        image = image.resize((size, size), Image.Resampling.NEAREST)

    if image.mode != "RGB":
        image = image.convert("RGB")

    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def create_image_payloads(png_data: bytes) -> list[bytearray]:
    """Create chunked payloads for PNG image upload.

    Protocol from derkalle4/python3-idotmatrix-library:
    - Split PNG into 4096-byte chunks
    - Each chunk gets a 9-byte header:
      [0-1] idk = (png_len + num_chunks) as int16 LE
      [2]   0x00
      [3]   0x00
      [4]   chunk_flag: 0x00 for first, 0x02 for subsequent
      [5-8] total PNG length as int32 LE
      [9+]  chunk data (up to 4096 bytes)
    """
    # Split PNG data into 4096-byte chunks
    png_chunks: list[bytes] = []
    offset = 0
    while offset < len(png_data):
        end = min(offset + MAX_CHUNK_SIZE, len(png_data))
        png_chunks.append(png_data[offset:end])
        offset = end

    idk = len(png_data) + len(png_chunks)
    idk_bytes = struct.pack("<h", idk)
    png_len_bytes = struct.pack("<i", len(png_data))

    payloads: list[bytearray] = []
    for i, chunk in enumerate(png_chunks):
        chunk_flag = 0x02 if i > 0 else 0x00
        header = (
            idk_bytes
            + bytearray([0x00, 0x00, chunk_flag])
            + png_len_bytes
        )
        payloads.append(bytearray(header) + bytearray(chunk))

    return payloads
