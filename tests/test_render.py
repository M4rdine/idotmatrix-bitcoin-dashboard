"""Tests for rendering utilities."""

from __future__ import annotations

import pytest
from PIL import Image

from src.render.colors import COLORS, RGB, price_change_color, status_to_color
from src.render.dashboard import render_dashboard
from src.render.text import measure_text, render_multiline, render_text_line
from src.data.agents import AgentStatus


class TestRGB:
    def test_rgb_creation(self) -> None:
        color = RGB(100, 150, 200)
        assert color.r == 100
        assert color.g == 150
        assert color.b == 200

    def test_rgb_tuple(self) -> None:
        color = RGB(10, 20, 30)
        assert color.tuple == (10, 20, 30)

    def test_rgb_with_brightness(self) -> None:
        color = RGB(200, 100, 50)
        dimmed = color.with_brightness(0.5)
        assert dimmed.r == 100
        assert dimmed.g == 50
        assert dimmed.b == 25

    def test_rgb_with_brightness_clamped(self) -> None:
        color = RGB(100, 100, 100)
        bright = color.with_brightness(2.0)
        assert bright.r == 100  # clamped to 1.0

    def test_rgb_blend(self) -> None:
        white = RGB(255, 255, 255)
        black = RGB(0, 0, 0)
        mid = white.blend(black, 0.5)
        assert mid.r == 127
        assert mid.g == 127
        assert mid.b == 127

    def test_rgb_is_immutable(self) -> None:
        color = RGB(1, 2, 3)
        with pytest.raises(AttributeError):
            color.r = 10  # type: ignore[misc]


class TestColorUtilities:
    def test_price_change_positive(self) -> None:
        color = price_change_color(5.0)
        assert color == COLORS.GREEN

    def test_price_change_negative(self) -> None:
        color = price_change_color(-3.0)
        assert color == COLORS.RED

    def test_price_change_neutral(self) -> None:
        color = price_change_color(0.1)
        assert color == COLORS.TEXT_DIM

    def test_status_to_color_online(self) -> None:
        assert status_to_color("online") == COLORS.STATUS_OK

    def test_status_to_color_error(self) -> None:
        assert status_to_color("error") == COLORS.STATUS_ERROR

    def test_status_to_color_unknown(self) -> None:
        assert status_to_color("something_weird") == COLORS.STATUS_OFFLINE

    def test_status_to_color_case_insensitive(self) -> None:
        assert status_to_color("ONLINE") == COLORS.STATUS_OK


class TestTextRendering:
    def test_render_text_line_returns_image(self) -> None:
        img = render_text_line("Hello", 32, 32)
        assert isinstance(img, Image.Image)
        assert img.size == (32, 32)
        assert img.mode == "RGB"

    def test_render_text_line_custom_size(self) -> None:
        img = render_text_line("Hi", 64, 64)
        assert img.size == (64, 64)

    def test_render_text_line_with_color(self) -> None:
        img = render_text_line("X", 16, 16, color=COLORS.RED, bg_color=COLORS.BLACK)
        # Check that not all pixels are black (text was rendered)
        pixels = list(img.getdata())
        has_non_black = any(p != (0, 0, 0) for p in pixels)
        assert has_non_black

    def test_render_text_centered(self) -> None:
        img = render_text_line("X", 32, 32, align="center")
        assert img.size == (32, 32)

    def test_render_multiline(self) -> None:
        lines = [
            ("Line 1", COLORS.WHITE),
            ("Line 2", COLORS.RED),
        ]
        img = render_multiline(lines, 64, 64)
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)

    def test_measure_text(self) -> None:
        width, height = measure_text("Hello")
        assert width > 0
        assert height > 0


class TestDashboard:
    def test_render_dashboard_16(self) -> None:
        img = render_dashboard(16)
        assert img.size == (16, 16)
        assert img.mode == "RGB"

    def test_render_dashboard_32(self) -> None:
        img = render_dashboard(32, btc_prices={"usd": 43000.0}, btc_change_24h=2.5)
        assert img.size == (32, 32)

    def test_render_dashboard_64(self) -> None:
        agents = [
            AgentStatus(name="bot-1", status="online", message="OK"),
            AgentStatus(name="bot-2", status="error", message="Timeout"),
        ]
        img = render_dashboard(
            64,
            btc_prices={"usd": 43000.0, "brl": 215000.0},
            btc_change_24h=-1.5,
            agents=agents,
        )
        assert img.size == (64, 64)

    def test_render_dashboard_no_data(self) -> None:
        img = render_dashboard(32)
        assert img.size == (32, 32)

    def test_render_dashboard_with_agents(self) -> None:
        agents = [
            AgentStatus(name=f"agent-{i}", status="online")
            for i in range(10)
        ]
        img = render_dashboard(64, agents=agents)
        assert img.size == (64, 64)
