"""Tests for Bitcoin data fetching."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.data.bitcoin import BitcoinData, fetch_bitcoin_price


class TestBitcoinData:
    def test_bitcoin_data_creation(self) -> None:
        data = BitcoinData(prices={"usd": 43000.0}, change_24h=2.5)
        assert data.prices["usd"] == 43000.0
        assert data.change_24h == 2.5

    def test_bitcoin_data_is_valid(self) -> None:
        data = BitcoinData(prices={"usd": 43000.0})
        assert data.is_valid is True

    def test_bitcoin_data_invalid_when_empty(self) -> None:
        data = BitcoinData()
        assert data.is_valid is False

    def test_bitcoin_data_is_immutable(self) -> None:
        data = BitcoinData(prices={"usd": 43000.0})
        with pytest.raises(AttributeError):
            data.change_24h = 5.0  # type: ignore[misc]

    def test_bitcoin_data_has_timestamp(self) -> None:
        data = BitcoinData(prices={"usd": 1.0})
        assert data.timestamp is not None


class TestFetchBitcoinPrice:
    @pytest.mark.asyncio
    async def test_fetch_success(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "bitcoin": {
                "usd": 43250.50,
                "brl": 215000.00,
                "usd_24h_change": 2.35,
            }
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("src.data.bitcoin.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_bitcoin_price(["usd", "brl"])

        assert result.is_valid
        assert result.prices["usd"] == 43250.50
        assert result.prices["brl"] == 215000.00
        assert result.change_24h == 2.35

    @pytest.mark.asyncio
    async def test_fetch_default_currencies(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "bitcoin": {
                "usd": 43000.0,
                "brl": 215000.0,
                "usd_24h_change": -1.0,
            }
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("src.data.bitcoin.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_bitcoin_price()

        assert "usd" in result.prices
        assert "brl" in result.prices

    @pytest.mark.asyncio
    async def test_fetch_handles_parse_error(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"unexpected": "format"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("src.data.bitcoin.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_bitcoin_price()

        # Should return empty BitcoinData, not raise
        assert not result.is_valid
