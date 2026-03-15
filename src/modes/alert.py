"""Full-screen color alert mode.

Fills the entire display with a solid color, optionally
with a short text message overlaid.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from src.render.colors import COLORS, RGB
from src.render.text import _get_font


logger = logging.getLogger(__name__)


@dataclass
class AlertMode:
    """Full-screen alert display mode.

    Shows a solid color background with an optional text overlay.
    Useful for critical notifications or visual indicators.
    """

    size: int
    color: RGB = field(default_factory=lambda: COLORS.RED)
    message: str = ""
    text_color: RGB = field(default_factory=lambda: COLORS.WHITE)
    _blink_state: bool = True
    _frame_count: int = 0
    blink: bool = False

    @property
    def name(self) -> str:
        return "alert"

    async def update_data(self) -> None:
        """No external data needed for alerts."""

    def set_alert(
        self,
        color: RGB,
        message: str = "",
        text_color: RGB = COLORS.WHITE,
        blink: bool = False,
    ) -> None:
        """Configure the alert display.

        Creates a new configuration without mutating internal state
        beyond the necessary display parameters.
        """
        self.color = color
        self.message = message
        self.text_color = text_color
        self.blink = blink

    def clear(self) -> None:
        """Reset alert to default state."""
        self.color = COLORS.RED
        self.message = ""
        self.text_color = COLORS.WHITE
        self.blink = False
        self._frame_count = 0

    def render(self) -> Image.Image:
        """Render the alert frame."""
        self._frame_count += 1

        if self.blink:
            self._blink_state = (self._frame_count // 5) % 2 == 0

        bg = self.color if self._blink_state else COLORS.BLACK
        image = Image.new("RGB", (self.size, self.size), bg.tuple)

        if self.message and self._blink_state:
            draw = ImageDraw.Draw(image)
            self._draw_centered_text(draw, self.message)

        return image

    def _draw_centered_text(self, draw: ImageDraw.ImageDraw, text: str) -> None:
        """Draw text centered on the display."""
        font_size = self._auto_font_size()
        font = _get_font(font_size)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = max(0, (self.size - text_width) // 2)
        y = max(0, (self.size - text_height) // 2)

        draw.text((x, y), text, fill=self.text_color.tuple, font=font)

    def _auto_font_size(self) -> int:
        """Choose font size based on display resolution."""
        if self.size <= 16:
            return 8
        if self.size <= 32:
            return 10
        return 14
