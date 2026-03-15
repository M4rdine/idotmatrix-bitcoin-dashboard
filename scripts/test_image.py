"""Test image display on 16x16: PNG upload + pixel-by-pixel fallback."""

import asyncio
import logging
import sys
import time

from bleak import BleakScanner
from PIL import Image, ImageDraw

sys.path.insert(0, ".")

from src.ble.client import IdmClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SIZE = 16


def create_btc_image() -> Image.Image:
    """Create BTC-themed 16x16 image: orange bg with B."""
    img = Image.new("RGB", (SIZE, SIZE), (255, 153, 0))
    draw = ImageDraw.Draw(img)
    w = (255, 255, 255)

    # Pixel art B for 16x16
    # Vertical bar
    for y in range(3, 13):
        draw.point((4, y), fill=w)
        draw.point((5, y), fill=w)
    # Top horizontal
    for x in range(6, 10):
        draw.point((x, 3), fill=w)
        draw.point((x, 4), fill=w)
    # Middle horizontal
    for x in range(6, 10):
        draw.point((x, 7), fill=w)
        draw.point((x, 8), fill=w)
    # Bottom horizontal
    for x in range(6, 10):
        draw.point((x, 11), fill=w)
        draw.point((x, 12), fill=w)
    # Right bumps
    draw.point((10, 5), fill=w)
    draw.point((10, 6), fill=w)
    draw.point((11, 5), fill=w)
    draw.point((11, 6), fill=w)
    draw.point((10, 9), fill=w)
    draw.point((10, 10), fill=w)
    draw.point((11, 9), fill=w)
    draw.point((11, 10), fill=w)

    return img


async def find_device():
    devices = await BleakScanner.discover(timeout=5)
    for d in devices:
        if d.name and d.name.startswith("IDM-"):
            return d
    return None


async def main():
    logger.info("Scanning for device...")
    device = await find_device()
    if not device:
        logger.error("No device found!")
        return

    async with IdmClient(device) as client:
        await client.power_on()
        await client.set_brightness(100)
        await asyncio.sleep(0.5)

        # Test 1: PNG upload - solid red
        logger.info("=== Test 1: PNG upload (solid red 16x16) ===")
        red_img = Image.new("RGB", (SIZE, SIZE), (255, 0, 0))
        await client.send_image(red_img, SIZE)
        logger.info("PNG sent! Red screen?")
        await asyncio.sleep(4)

        # Test 2: PNG upload - solid green
        logger.info("=== Test 2: PNG upload (solid green 16x16) ===")
        green_img = Image.new("RGB", (SIZE, SIZE), (0, 255, 0))
        await client.send_image(green_img, SIZE)
        logger.info("PNG sent! Green screen?")
        await asyncio.sleep(4)

        # Test 3: PNG upload - BTC logo
        logger.info("=== Test 3: PNG upload (BTC B 16x16) ===")
        btc_img = create_btc_image()
        await client.send_image(btc_img, SIZE)
        logger.info("PNG sent! BTC B?")
        await asyncio.sleep(4)

        # Test 4: Pixel-by-pixel (full 16x16 = 256 pixels, should be fast)
        logger.info("=== Test 4: Pixel-by-pixel BTC logo (16x16) ===")
        t0 = time.time()
        await client.fill_screen_pixels(btc_img, SIZE)
        elapsed = time.time() - t0
        logger.info("256 pixels sent in %.1fs!", elapsed)

        logger.info("Waiting 10s...")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
