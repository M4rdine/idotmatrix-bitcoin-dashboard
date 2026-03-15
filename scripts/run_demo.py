"""Demo: connects to display, shows BTC price for 30 seconds, then exits."""

import asyncio
import logging
import sys

sys.path.insert(0, ".")

from src.ble.client import IdmClient
from src.ble.scanner import scan_for_device
from src.data.bitcoin import fetch_bitcoin_price
from src.render.dashboard import render_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DISPLAY_SIZE = 32
DEMO_DURATION = 30
FRAME_INTERVAL = 2


async def main():
    logger.info("Scanning for iDotMatrix device...")
    device = await scan_for_device(prefix="IDM-", scan_duration=5)
    if not device:
        logger.error("No device found!")
        return

    async with IdmClient(device) as client:
        await client.power_on()
        await client.set_brightness(80)
        logger.info("Connected! Fetching BTC price...")

        btc_data = await fetch_bitcoin_price(["brl", "usd"])
        logger.info("BTC: %s (24h: %.2f%%)", btc_data.prices, btc_data.change_24h)

        elapsed = 0
        while elapsed < DEMO_DURATION:
            # Re-fetch every 15 seconds
            if elapsed > 0 and elapsed % 15 == 0:
                try:
                    btc_data = await fetch_bitcoin_price(["brl", "usd"])
                    logger.info("Refreshed: %s", btc_data.prices)
                except Exception:
                    logger.warning("Price refresh failed, using cached data")

            frame = render_dashboard(
                size=DISPLAY_SIZE,
                btc_prices=btc_data.prices,
                btc_change_24h=btc_data.change_24h,
            )
            await client.send_image(frame, DISPLAY_SIZE)
            logger.info("Frame sent (t=%ds/%ds)", elapsed, DEMO_DURATION)

            await asyncio.sleep(FRAME_INTERVAL)
            elapsed += FRAME_INTERVAL

        logger.info("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
