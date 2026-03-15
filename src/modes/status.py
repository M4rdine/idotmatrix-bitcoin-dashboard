"""Agent status dashboard mode.

Displays the status of monitored agents as colored indicators
with names on the LED display.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from PIL import Image, ImageDraw

from src.data.agents import AgentStore
from src.render.colors import COLORS, status_to_color
from src.render.text import _get_font


logger = logging.getLogger(__name__)


@dataclass
class StatusMode:
    """Agent status display mode.

    Shows agent names with colored status indicators.
    Layout adapts to display size.
    """

    size: int

    @property
    def name(self) -> str:
        return "status"

    async def update_data(self) -> None:
        """No external data to fetch -- reads from in-memory store."""

    def render(self) -> Image.Image:
        """Render the agent status display."""
        image = Image.new("RGB", (self.size, self.size), COLORS.BG_DARK.tuple)
        draw = ImageDraw.Draw(image)
        store = AgentStore.get_instance()
        agents = store.get_all()

        if not agents:
            return self._render_empty(image, draw)

        if self.size <= 16:
            return self._render_dots_only(image, draw, agents)
        if self.size <= 32:
            return self._render_compact(image, draw, agents)
        return self._render_full(image, draw, agents)

    def _render_empty(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:
        font = _get_font(8)
        draw.text((1, self.size // 2 - 4), "NO AGT", fill=COLORS.TEXT_DIM.tuple, font=font)
        return image

    def _render_dots_only(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        agents: list,
    ) -> Image.Image:
        """16x16: Just colored dots in a grid."""
        x, y = 1, 1
        dot_size = 2
        spacing = 4

        for agent in agents:
            if y + dot_size > self.size:
                break
            color = status_to_color(agent.status)
            draw.rectangle(
                [(x, y), (x + dot_size, y + dot_size)],
                fill=color.tuple,
            )
            x += spacing
            if x + dot_size > self.size:
                x = 1
                y += spacing

        return image

    def _render_compact(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        agents: list,
    ) -> Image.Image:
        """32x32: Dot + short name per line."""
        font = _get_font(8)

        draw.rectangle([(0, 0), (self.size - 1, 7)], fill=COLORS.BG_HEADER.tuple)
        draw.text((1, 0), "AGENTS", fill=COLORS.TEXT_BRIGHT.tuple, font=font)

        y = 9
        for agent in agents[:3]:
            if y + 8 > self.size:
                break
            color = status_to_color(agent.status)
            draw.rectangle([(1, y + 2), (3, y + 4)], fill=color.tuple)
            name = agent.name[:5]
            draw.text((5, y), name, fill=COLORS.TEXT_DIM.tuple, font=font)
            y += 8

        return image

    def _render_full(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        agents: list,
    ) -> Image.Image:
        """64x64: Full status list with names and messages."""
        font = _get_font(8)

        draw.rectangle([(0, 0), (self.size - 1, 10)], fill=COLORS.BG_HEADER.tuple)
        draw.text((2, 1), "AGENT STATUS", fill=COLORS.TEXT_BRIGHT.tuple, font=font)
        draw.line([(0, 11), (self.size - 1, 11)], fill=COLORS.BORDER.tuple)

        y = 13
        for agent in agents[:5]:
            if y + 10 > self.size:
                break
            color = status_to_color(agent.status)

            # Status dot
            draw.rectangle([(2, y + 1), (4, y + 3)], fill=color.tuple)

            # Agent name
            name = agent.name[:10]
            draw.text((7, y), name, fill=COLORS.TEXT_DIM.tuple, font=font)

            # Status text on next line if space
            if agent.message and y + 18 <= self.size:
                msg = agent.message[:12]
                draw.text((7, y + 8), msg, fill=color.tuple, font=font)
                y += 18
            else:
                y += 10

        return image
