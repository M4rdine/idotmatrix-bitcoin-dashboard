"""Tests for iDotMatrix protocol commands."""

from __future__ import annotations

import pytest
from PIL import Image

from src.protocol.commands import (
    Color,
    build_brightness_command,
    build_fullscreen_color_command,
    build_image_header,
    build_pixel_command,
    build_power_command,
    build_text_header,
    build_text_metadata,
    encode_image_rgb,
)


class TestColor:
    def test_valid_color(self) -> None:
        color = Color(255, 128, 0)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_color_to_bytes(self) -> None:
        color = Color(10, 20, 30)
        assert color.to_bytes() == bytes([10, 20, 30])

    def test_invalid_color_raises(self) -> None:
        with pytest.raises(ValueError, match="Color channel"):
            Color(256, 0, 0)

    def test_negative_color_raises(self) -> None:
        with pytest.raises(ValueError, match="Color channel"):
            Color(-1, 0, 0)

    def test_color_is_immutable(self) -> None:
        color = Color(1, 2, 3)
        with pytest.raises(AttributeError):
            color.r = 10  # type: ignore[misc]


class TestPowerCommand:
    def test_power_on(self) -> None:
        cmd = build_power_command(on=True)
        assert cmd == bytearray([5, 0, 7, 1, 1])

    def test_power_off(self) -> None:
        cmd = build_power_command(on=False)
        assert cmd == bytearray([5, 0, 7, 1, 0])

    def test_power_command_length(self) -> None:
        cmd = build_power_command(on=True)
        assert len(cmd) == 5


class TestBrightnessCommand:
    def test_brightness_50(self) -> None:
        cmd = build_brightness_command(50)
        assert cmd == bytearray([5, 0, 4, 0x80, 50])

    def test_brightness_0(self) -> None:
        cmd = build_brightness_command(0)
        assert cmd[4] == 0

    def test_brightness_100(self) -> None:
        cmd = build_brightness_command(100)
        assert cmd[4] == 100

    def test_brightness_clamped_above(self) -> None:
        cmd = build_brightness_command(150)
        assert cmd[4] == 100

    def test_brightness_clamped_below(self) -> None:
        cmd = build_brightness_command(-10)
        assert cmd[4] == 0


class TestFullscreenColorCommand:
    def test_red(self) -> None:
        cmd = build_fullscreen_color_command(255, 0, 0)
        assert cmd == bytearray([7, 0, 2, 2, 255, 0, 0])

    def test_green(self) -> None:
        cmd = build_fullscreen_color_command(0, 255, 0)
        assert cmd == bytearray([7, 0, 2, 2, 0, 255, 0])

    def test_white(self) -> None:
        cmd = build_fullscreen_color_command(255, 255, 255)
        assert cmd == bytearray([7, 0, 2, 2, 255, 255, 255])

    def test_command_length(self) -> None:
        cmd = build_fullscreen_color_command(0, 0, 0)
        assert len(cmd) == 7


class TestPixelCommand:
    def test_pixel_at_origin(self) -> None:
        cmd = build_pixel_command(0, 0, 255, 0, 0)
        assert cmd == bytearray([10, 0, 5, 1, 0, 255, 0, 0, 0, 0])

    def test_pixel_at_position(self) -> None:
        cmd = build_pixel_command(15, 15, 0, 255, 0)
        assert cmd[8] == 15
        assert cmd[9] == 15

    def test_pixel_command_length(self) -> None:
        cmd = build_pixel_command(0, 0, 0, 0, 0)
        assert len(cmd) == 10


class TestImageHeader:
    def test_header_16x16(self) -> None:
        header = build_image_header(16)
        assert len(header) == 9
        # total_len = 9 + 16*16*3 = 777
        assert header[0] == 777 & 0xFF
        assert header[1] == (777 >> 8) & 0xFF
        assert header[5] == 1  # size code for 16

    def test_header_32x32(self) -> None:
        header = build_image_header(32)
        assert header[5] == 2  # size code for 32
        total_len = 9 + 32 * 32 * 3
        assert header[0] == total_len & 0xFF
        assert header[1] == (total_len >> 8) & 0xFF

    def test_header_64x64(self) -> None:
        header = build_image_header(64)
        assert header[5] == 3  # size code for 64

    def test_invalid_size_raises(self) -> None:
        with pytest.raises(ValueError, match="Display size must be"):
            build_image_header(48)

    def test_header_num_frames(self) -> None:
        header = build_image_header(32)
        # num_frames at bytes 7-8, little-endian = 1
        assert header[7] == 1
        assert header[8] == 0


class TestTextHeader:
    def test_text_header_length(self) -> None:
        header = build_text_header()
        assert len(header) == 16

    def test_text_header_color(self) -> None:
        header = build_text_header(color_r=255, color_g=0, color_b=128)
        assert header[13] == 255
        assert header[14] == 0
        assert header[15] == 128


class TestTextMetadata:
    def test_metadata_length(self) -> None:
        meta = build_text_metadata("Hello")
        assert len(meta) == 13

    def test_metadata_font_size(self) -> None:
        meta = build_text_metadata("Hi", font_size=16)
        assert meta[0] == 16

    def test_metadata_bold(self) -> None:
        meta = build_text_metadata("Hi", bold=True)
        assert meta[1] & 0x01

    def test_metadata_italic(self) -> None:
        meta = build_text_metadata("Hi", italic=True)
        assert meta[1] & 0x02


class TestEncodeImageRGB:
    def test_encode_32x32(self) -> None:
        img = Image.new("RGB", (32, 32), (255, 0, 0))
        data = encode_image_rgb(img, 32)
        assert len(data) == 32 * 32 * 3
        # First pixel should be red
        assert data[0] == 255
        assert data[1] == 0
        assert data[2] == 0

    def test_encode_resizes(self) -> None:
        img = Image.new("RGB", (64, 64), (0, 255, 0))
        data = encode_image_rgb(img, 32)
        assert len(data) == 32 * 32 * 3

    def test_encode_converts_rgba(self) -> None:
        img = Image.new("RGBA", (16, 16), (0, 0, 255, 128))
        data = encode_image_rgb(img, 16)
        assert len(data) == 16 * 16 * 3

    def test_encode_invalid_size(self) -> None:
        img = Image.new("RGB", (32, 32))
        with pytest.raises(ValueError):
            encode_image_rgb(img, 48)
