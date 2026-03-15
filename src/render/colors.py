"""Color constants and utilities for rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RGB:
    """Immutable RGB color."""

    r: int
    g: int
    b: int

    @property
    def tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def with_brightness(self, factor: float) -> "RGB":
        """Return a new color with adjusted brightness (0.0 to 1.0)."""
        clamped = max(0.0, min(1.0, factor))
        return RGB(
            r=int(self.r * clamped),
            g=int(self.g * clamped),
            b=int(self.b * clamped),
        )

    def blend(self, other: "RGB", ratio: float = 0.5) -> "RGB":
        """Blend this color with another. ratio=0 means self, ratio=1 means other."""
        clamped = max(0.0, min(1.0, ratio))
        return RGB(
            r=int(self.r * (1 - clamped) + other.r * clamped),
            g=int(self.g * (1 - clamped) + other.g * clamped),
            b=int(self.b * (1 - clamped) + other.b * clamped),
        )


class COLORS:
    """Predefined color constants for LED display."""

    BLACK = RGB(0, 0, 0)
    WHITE = RGB(255, 255, 255)
    RED = RGB(255, 0, 0)
    GREEN = RGB(0, 255, 0)
    BLUE = RGB(0, 0, 255)
    YELLOW = RGB(255, 255, 0)
    CYAN = RGB(0, 255, 255)
    MAGENTA = RGB(255, 0, 255)
    ORANGE = RGB(255, 165, 0)

    # Bitcoin colors
    BTC_ORANGE = RGB(247, 147, 26)
    BTC_GOLD = RGB(255, 215, 0)

    # Status colors
    STATUS_OK = RGB(0, 200, 0)
    STATUS_WARN = RGB(255, 200, 0)
    STATUS_ERROR = RGB(255, 0, 0)
    STATUS_OFFLINE = RGB(100, 100, 100)

    # UI colors
    BG_DARK = RGB(5, 5, 10)
    BG_HEADER = RGB(20, 20, 40)
    TEXT_DIM = RGB(120, 120, 120)
    TEXT_BRIGHT = RGB(220, 220, 220)
    BORDER = RGB(40, 40, 60)


def price_change_color(change_percent: float) -> RGB:
    """Return green for positive change, red for negative, gray for neutral."""
    if change_percent > 0.5:
        return COLORS.GREEN
    if change_percent < -0.5:
        return COLORS.RED
    return COLORS.TEXT_DIM


def status_to_color(status: str) -> RGB:
    """Map a status string to a color."""
    status_map = {
        "online": COLORS.STATUS_OK,
        "ok": COLORS.STATUS_OK,
        "running": COLORS.STATUS_OK,
        "warning": COLORS.STATUS_WARN,
        "degraded": COLORS.STATUS_WARN,
        "error": COLORS.STATUS_ERROR,
        "offline": COLORS.STATUS_OFFLINE,
        "unknown": COLORS.STATUS_OFFLINE,
    }
    return status_map.get(status.lower(), COLORS.STATUS_OFFLINE)
