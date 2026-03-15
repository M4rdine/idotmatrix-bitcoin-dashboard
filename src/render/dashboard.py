"""Dashboard layout renderer for the LED display.

Composes multiple data elements (BTC price, agent statuses) into
a single display-sized image.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from src.data.agents import AgentStatus
from src.render.colors import COLORS, RGB, price_change_color, status_to_color
from src.render.text import _get_font


def render_dashboard(
    size: int,
    btc_prices: dict[str, float] | None = None,
    btc_change_24h: float = 0.0,
    agents: list[AgentStatus] | None = None,
) -> Image.Image:
    """Render a complete dashboard image.

    Layout varies by display size:
    - 16x16: BTC price only (very compact)
    - 32x32: BTC price + up to 3 agent status dots
    - 64x64: Full dashboard with labels, prices, and agent list

    Args:
        size: Display resolution (16, 32, or 64).
        btc_prices: Dict of currency -> price (e.g. {"usd": 43000.0}).
        btc_change_24h: 24h price change percentage.
        agents: List of agent status objects.

    Returns:
        A Pillow Image at the specified resolution.
    """
    image = Image.new("RGB", (size, size), COLORS.BG_DARK.tuple)
    draw = ImageDraw.Draw(image)

    if size <= 16:
        return _render_compact(image, draw, size, btc_prices, btc_change_24h)
    if size <= 32:
        return _render_medium(image, draw, size, btc_prices, btc_change_24h, agents)
    return _render_full(image, draw, size, btc_prices, btc_change_24h, agents)


def _render_compact(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    size: int,
    btc_prices: dict[str, float] | None,
    change: float,
) -> Image.Image:
    """16x16 layout: BTC price only."""
    font = _get_font(8)

    # BTC icon indicator (top-left pixel)
    draw.rectangle([(0, 0), (2, 2)], fill=COLORS.BTC_ORANGE.tuple)

    if btc_prices:
        price = next(iter(btc_prices.values()), 0)
        price_text = _format_price_compact(price)
        color = price_change_color(change)
        draw.text((0, 4), price_text, fill=color.tuple, font=font)

    # Change direction arrow
    arrow_color = price_change_color(change)
    if change > 0:
        _draw_up_arrow(draw, size - 4, 0, arrow_color)
    elif change < 0:
        _draw_down_arrow(draw, size - 4, 0, arrow_color)

    return image


def _render_medium(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    size: int,
    btc_prices: dict[str, float] | None,
    change: float,
    agents: list[AgentStatus] | None,
) -> Image.Image:
    """32x32 layout: BTC price + agent status dots."""
    font = _get_font(8)

    # Header bar
    draw.rectangle([(0, 0), (size - 1, 7)], fill=COLORS.BG_HEADER.tuple)
    draw.text((1, 0), "BTC", fill=COLORS.BTC_ORANGE.tuple, font=font)

    # Price
    y = 9
    if btc_prices:
        for currency, price in btc_prices.items():
            label = currency.upper()
            price_str = _format_price_short(price, currency)
            color = price_change_color(change)
            draw.text((1, y), f"{label}", fill=COLORS.TEXT_DIM.tuple, font=font)
            draw.text((1, y + 8), price_str, fill=color.tuple, font=font)
            y += 17

    # Agent status dots (bottom row)
    if agents:
        dot_y = size - 4
        dot_x = 1
        for agent in agents[:6]:
            dot_color = status_to_color(agent.status)
            draw.rectangle(
                [(dot_x, dot_y), (dot_x + 2, dot_y + 2)],
                fill=dot_color.tuple,
            )
            dot_x += 4

    return image


def _render_full(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    size: int,
    btc_prices: dict[str, float] | None,
    change: float,
    agents: list[AgentStatus] | None,
) -> Image.Image:
    """64x64 layout: Full dashboard."""
    font_sm = _get_font(8)
    font_md = _get_font(10)

    # Header
    draw.rectangle([(0, 0), (size - 1, 10)], fill=COLORS.BG_HEADER.tuple)
    draw.text((2, 1), "BTC DASHBOARD", fill=COLORS.BTC_ORANGE.tuple, font=font_sm)

    # Separator line
    draw.line([(0, 11), (size - 1, 11)], fill=COLORS.BORDER.tuple)

    # Price section
    y = 13
    if btc_prices:
        for currency, price in btc_prices.items():
            label = currency.upper()
            price_str = _format_price_full(price, currency)
            color = price_change_color(change)

            draw.text((2, y), f"{label}:", fill=COLORS.TEXT_DIM.tuple, font=font_sm)
            draw.text((2, y + 9), price_str, fill=color.tuple, font=font_md)
            y += 20

    # Change percentage
    if change != 0:
        change_str = f"{change:+.1f}%"
        change_color = price_change_color(change)
        draw.text((2, y), "24h:", fill=COLORS.TEXT_DIM.tuple, font=font_sm)
        draw.text((20, y), change_str, fill=change_color.tuple, font=font_sm)
        y += 11

    # Separator
    draw.line([(0, y), (size - 1, y)], fill=COLORS.BORDER.tuple)
    y += 2

    # Agent status section
    if agents:
        draw.text((2, y), "AGENTS", fill=COLORS.TEXT_BRIGHT.tuple, font=font_sm)
        y += 10

        for agent in agents[:4]:
            dot_color = status_to_color(agent.status)
            draw.rectangle(
                [(2, y + 1), (4, y + 3)],
                fill=dot_color.tuple,
            )
            name = agent.name[:8]
            draw.text((7, y), name, fill=COLORS.TEXT_DIM.tuple, font=font_sm)
            y += 9

    return image


def _format_price_compact(price: float) -> str:
    """Format price for 16x16 display (very short)."""
    if price >= 1_000_000:
        return f"{price / 1_000_000:.0f}M"
    if price >= 1_000:
        return f"{price / 1_000:.0f}k"
    return f"{price:.0f}"


def _format_price_short(price: float, currency: str) -> str:
    """Format price for 32x32 display."""
    if currency in ("brl",) and price >= 1_000:
        return f"{price / 1_000:.0f}k"
    if price >= 1_000:
        return f"{price / 1_000:.1f}k"
    return f"{price:.0f}"


def _format_price_full(price: float, currency: str) -> str:
    """Format price for 64x64 display with more detail."""
    symbol_map = {"usd": "$", "brl": "R$", "eur": "E", "gbp": "L"}
    symbol = symbol_map.get(currency, "")

    if price >= 1_000_000:
        return f"{symbol}{price / 1_000_000:.2f}M"
    if price >= 1_000:
        return f"{symbol}{price:,.0f}"
    return f"{symbol}{price:.2f}"


def _draw_up_arrow(draw: ImageDraw.ImageDraw, x: int, y: int, color: RGB) -> None:
    """Draw a small upward arrow."""
    draw.point((x + 1, y), fill=color.tuple)
    draw.point((x, y + 1), fill=color.tuple)
    draw.point((x + 1, y + 1), fill=color.tuple)
    draw.point((x + 2, y + 1), fill=color.tuple)


def _draw_down_arrow(draw: ImageDraw.ImageDraw, x: int, y: int, color: RGB) -> None:
    """Draw a small downward arrow."""
    draw.point((x, y), fill=color.tuple)
    draw.point((x + 1, y), fill=color.tuple)
    draw.point((x + 2, y), fill=color.tuple)
    draw.point((x + 1, y + 1), fill=color.tuple)
