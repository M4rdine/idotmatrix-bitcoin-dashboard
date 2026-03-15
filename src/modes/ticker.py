"""BTC price scrolling ticker mode.

Displays the current Bitcoin price with a scrolling effect
for text that exceeds the display width.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from src.data.bitcoin import BitcoinData, fetch_bitcoin_price
from src.render.colors import COLORS, price_change_color
from src.render.text import _get_font


logger = logging.getLogger(__name__)

REFRESH_INTERVAL = 60  # seconds between price refreshes


@dataclass
class TickerMode:
    """BTC price ticker display mode.

    Shows the Bitcoin price with a scrolling animation for longer text.
    Periodically refreshes the price data.
    """

    size: int
    currencies: list[str] = field(default_factory=lambda: ["usd", "brl"])
    _btc_data: BitcoinData | None = None
    _scroll_offset: int = 0
    _frame_count: int = 0

    @property
    def name(self) -> str:
        return "ticker"

    async def update_data(self) -> None:
        """Fetch fresh Bitcoin price data."""
        try:
            self._btc_data = await fetch_bitcoin_price(self.currencies)
        except Exception as exc:
            logger.error("Failed to update ticker data: %s", exc)

    def render(self) -> Image.Image:
        """Render the current ticker frame."""
        image = Image.new("RGB", (self.size, self.size), COLORS.BG_DARK.tuple)
        draw = ImageDraw.Draw(image)

        if self._btc_data is None or not self._btc_data.is_valid:
            return self._render_loading(image, draw)

        return self._render_prices(image, draw)

    def _render_loading(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:
        font = _get_font(8)
        draw.text((1, self.size // 2 - 4), "LOAD..", fill=COLORS.TEXT_DIM.tuple, font=font)
        return image

    def _render_prices(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
    ) -> Image.Image:
        font = _get_font(8)
        change = self._btc_data.change_24h if self._btc_data else 0.0
        color = price_change_color(change)

        # BTC header
        draw.rectangle([(0, 0), (self.size - 1, 7)], fill=COLORS.BG_HEADER.tuple)

        btc_label = "BTC"
        if self._btc_data and change != 0:
            arrow = "^" if change > 0 else "v"
            btc_label = f"BTC {arrow}"

        draw.text((1, 0), btc_label, fill=COLORS.BTC_ORANGE.tuple, font=font)

        # Prices - scroll through currencies
        y = 9
        if self._btc_data:
            for currency, price in self._btc_data.prices.items():
                if y + 8 > self.size:
                    break
                price_text = self._format_ticker_price(price, currency)
                label = currency.upper()

                draw.text((1, y), label, fill=COLORS.TEXT_DIM.tuple, font=font)
                y += 8

                # Scroll long price text
                text_x = self._calculate_scroll_x(price_text, font, draw)
                draw.text((text_x, y), price_text, fill=color.tuple, font=font)
                y += 9

        self._frame_count += 1
        self._scroll_offset = (self._scroll_offset + 1) % 100

        return image

    def _calculate_scroll_x(
        self,
        text: str,
        font: object,
        draw: ImageDraw.ImageDraw,
    ) -> int:
        """Calculate X position for scrolling text."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= self.size - 2:
            return 1

        # Scroll: move text left over time
        total_scroll = text_width - self.size + 4
        phase = self._scroll_offset % (total_scroll * 2)
        if phase < total_scroll:
            return 1 - phase
        return 1 - (total_scroll * 2 - phase)

    def _format_ticker_price(self, price: float, currency: str) -> str:
        """Format price for ticker display."""
        symbol_map = {"usd": "$", "brl": "R$", "eur": "E", "gbp": "L"}
        symbol = symbol_map.get(currency, "")

        if price >= 1_000_000:
            return f"{symbol}{price:,.0f}"
        if price >= 1_000:
            return f"{symbol}{price:,.0f}"
        return f"{symbol}{price:.2f}"
