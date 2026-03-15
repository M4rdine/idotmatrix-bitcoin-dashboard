"""Live BTC ticker on 16x16 LED matrix with pixel-perfect scrolling marquee.

Uses custom 3x5 bitmap font. Price updates every 5 minutes.
Scrolls continuously. Auto-reconnects on BLE disconnect.
Runs forever until Ctrl+C.
"""

import asyncio
import logging
import signal
import sys
import time
import traceback

import httpx
from bleak import BleakClient, BleakScanner
from PIL import Image

sys.path.insert(0, ".")

from src.render.pixel_font import (
    draw_btc_icon,
    draw_text,
    measure_text,
)
from src.protocol.commands import (
    WRITE_UUID,
    build_brightness_command,
    build_image_mode_command,
    build_power_command,
    create_image_payloads,
    pil_image_to_png_bytes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SIZE = 16
PRICE_REFRESH_SECONDS = 300  # 5 minutes
SCROLL_SPEED = 0.12

GREEN = (0, 200, 0)
RED = (255, 50, 50)
BTC_ORANGE = (247, 147, 26)
BG = (0, 0, 0)


def render_scroll_frame(
    text: str,
    scroll_offset: int,
    color: tuple[int, int, int],
) -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE), BG)

    icon_w = 6
    gap = 3
    text_w = measure_text(text)
    total_w = icon_w + gap + text_w + gap

    pos = -(scroll_offset % total_w)
    text_y = 6

    for offset in (pos, pos + total_w):
        draw_btc_icon(img, offset, 4, BTC_ORANGE)
        draw_text(img, text, offset + icon_w + gap, text_y, color)

    return img


async def fetch_btc_price() -> dict | None:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()["bitcoin"]
            return {
                "price": data["usd"],
                "change": data.get("usd_24h_change", 0),
            }
    except Exception as exc:
        logger.error("Price fetch failed: %s", exc)
        return None


async def find_device():
    devices = await BleakScanner.discover(timeout=5)
    for d in devices:
        if d.name and d.name.startswith("IDM-"):
            return d
    return None


async def send_image_raw(ble_client: BleakClient, pil_image: Image.Image) -> None:
    """Send image directly via BleakClient (no wrapper class dependency)."""
    png_data = pil_image_to_png_bytes(pil_image, SIZE)

    # Enter image mode
    await ble_client.write_gatt_char(WRITE_UUID, build_image_mode_command(enable=True), response=True)
    await asyncio.sleep(0.05)

    # Send PNG payloads
    payloads = create_image_payloads(png_data)
    char = ble_client.services.get_characteristic(WRITE_UUID)
    mtu = char.max_write_without_response_size if char else 512

    for payload in payloads:
        for i in range(0, len(payload), mtu):
            chunk = payload[i:i + mtu]
            await ble_client.write_gatt_char(WRITE_UUID, chunk, response=False)
        await asyncio.sleep(0.01)


async def main():
    running = True

    def stop():
        nonlocal running
        running = False

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop)

    price_data = None
    last_fetch = 0.0
    scroll_offset = 0

    logger.info("BTC Live Ticker - runs forever (Ctrl+C to stop)")

    while running:
        device = await find_device()
        if not device:
            logger.error("No device found, retrying in 10s...")
            await asyncio.sleep(10)
            continue

        ble_client = BleakClient(device, timeout=10)
        try:
            await ble_client.connect()
            logger.info("Connected to %s", device.name)

            # Setup
            await ble_client.write_gatt_char(WRITE_UUID, build_power_command(on=True), response=True)
            await asyncio.sleep(0.1)
            await ble_client.write_gatt_char(WRITE_UUID, build_brightness_command(80), response=True)
            await asyncio.sleep(0.1)

            logger.info("Marquee running (price updates every 5 min)")

            while running and ble_client.is_connected:
                now = time.time()

                # Fetch price every 5 min
                if price_data is None or (now - last_fetch) >= PRICE_REFRESH_SECONDS:
                    new_data = await fetch_btc_price()
                    if new_data:
                        price_data = new_data
                        last_fetch = now
                        logger.info(
                            "BTC: $%s (24h: %+.2f%%)",
                            f"{price_data['price']:,.0f}",
                            price_data["change"],
                        )
                    elif price_data is None:
                        await asyncio.sleep(5)
                        continue

                price = price_data["price"]
                change = price_data["change"]
                sign = "+" if change >= 0 else ""
                display_text = f"{price:,.0f} {sign}{change:.1f}%"
                color = GREEN if change >= 0 else RED

                frame = render_scroll_frame(display_text, scroll_offset, color)

                try:
                    await send_image_raw(ble_client, frame)
                except Exception:
                    logger.warning("Send failed, breaking to reconnect...")
                    break

                scroll_offset += 1
                await asyncio.sleep(SCROLL_SPEED)

            if not ble_client.is_connected:
                logger.warning("BLE disconnected, reconnecting in 3s...")

        except Exception as exc:
            logger.error("Connection error: %s", exc)

        finally:
            try:
                if ble_client.is_connected:
                    await ble_client.disconnect()
            except Exception:
                pass

        if running:
            await asyncio.sleep(3)

    logger.info("Shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
