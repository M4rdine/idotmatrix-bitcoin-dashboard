"""Bitcoin price data fetcher using CoinGecko free API."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx


logger = logging.getLogger(__name__)

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
PRICE_ENDPOINT = f"{COINGECKO_BASE_URL}/simple/price"
REQUEST_TIMEOUT = 10.0


@dataclass(frozen=True)
class BitcoinData:
    """Immutable snapshot of Bitcoin price data."""

    prices: dict[str, float] = field(default_factory=dict)
    change_24h: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_valid(self) -> bool:
        return len(self.prices) > 0


async def fetch_bitcoin_price(
    currencies: list[str] | None = None,
) -> BitcoinData:
    """Fetch current Bitcoin price from CoinGecko free API.

    Args:
        currencies: List of currency codes (e.g. ["usd", "brl"]).
                   Defaults to ["usd", "brl"].

    Returns:
        BitcoinData with current prices and 24h change.

    Raises:
        httpx.HTTPError: If the API request fails.
    """
    if currencies is None:
        currencies = ["usd", "brl"]

    vs_currencies = ",".join(currencies)
    params = {
        "ids": "bitcoin",
        "vs_currencies": vs_currencies,
        "include_24hr_change": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(PRICE_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()

        bitcoin = data.get("bitcoin", {})

        prices: dict[str, float] = {}
        for currency in currencies:
            price = bitcoin.get(currency)
            if price is not None:
                prices[currency] = float(price)

        change_key = f"{currencies[0]}_24h_change"
        change_24h = float(bitcoin.get(change_key, 0.0))

        result = BitcoinData(
            prices=prices,
            change_24h=change_24h,
            timestamp=datetime.now(timezone.utc),
        )
        logger.info(
            "Fetched BTC prices: %s (24h change: %.2f%%)",
            prices,
            change_24h,
        )
        return result

    except httpx.HTTPError as exc:
        logger.error("Failed to fetch Bitcoin price: %s", exc)
        raise
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("Failed to parse CoinGecko response: %s", exc)
        return BitcoinData()
