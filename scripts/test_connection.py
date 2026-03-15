"""Quick connection test: connects to the display and sends a test pattern."""

import asyncio
import sys

from bleak import BleakScanner
from PIL import Image, ImageDraw

sys.path.insert(0, ".")

from src.ble.client import IdmClient
from src.protocol.commands import build_fullscreen_color_command, WRITE_UUID


DEVICE_PREFIX = "IDM-"
DISPLAY_SIZE = 32


async def find_device():
    print(f"Scanning for {DEVICE_PREFIX}* devices...")
    devices = await BleakScanner.discover(timeout=5)
    for device in devices:
        if device.name and device.name.startswith(DEVICE_PREFIX):
            print(f"Found: {device.name} ({device.address})")
            return device
    return None


def create_test_image(size: int) -> Image.Image:
    """Create a simple test pattern: BTC orange background with white B."""
    img = Image.new("RGB", (size, size), (255, 153, 0))  # BTC orange
    draw = ImageDraw.Draw(img)

    # Draw a centered "B" (pixel art style for 32x32)
    if size >= 32:
        # Simple block letter B
        white = (255, 255, 255)
        # Vertical bar
        for y in range(8, 24):
            for x in range(10, 14):
                draw.point((x, y), fill=white)
        # Top horizontal
        for x in range(14, 20):
            draw.point((x, 8), fill=white)
            draw.point((x, 9), fill=white)
        # Middle horizontal
        for x in range(14, 20):
            draw.point((x, 15), fill=white)
            draw.point((x, 16), fill=white)
        # Bottom horizontal
        for x in range(14, 20):
            draw.point((x, 22), fill=white)
            draw.point((x, 23), fill=white)
        # Right bumps
        for y in range(10, 15):
            draw.point((20, y), fill=white)
            draw.point((21, y), fill=white)
        for y in range(17, 22):
            draw.point((20, y), fill=white)
            draw.point((21, y), fill=white)
    else:
        draw.rectangle([2, 2, size - 3, size - 3], outline=(255, 255, 255))

    return img


async def main():
    device = await find_device()
    if not device:
        print("No iDotMatrix device found! Make sure it's powered on.")
        return

    async with IdmClient(device) as client:
        print("Connected! Testing commands...")

        # Step 1: Power on
        print("  1. Power ON")
        await client.power_on()
        await asyncio.sleep(0.5)

        # Step 2: Set brightness
        print("  2. Setting brightness to 80%")
        await client.set_brightness(80)
        await asyncio.sleep(0.5)

        # Step 3: Send test image (BTC logo)
        print("  3. Sending BTC test image...")
        test_img = create_test_image(DISPLAY_SIZE)
        await client.send_image(test_img, DISPLAY_SIZE)

        print("\nSuccess! You should see a BTC 'B' on the display.")
        print("Press Ctrl+C to disconnect.")

        try:
            await asyncio.sleep(30)
        except KeyboardInterrupt:
            pass

        print("Disconnecting...")


if __name__ == "__main__":
    asyncio.run(main())
