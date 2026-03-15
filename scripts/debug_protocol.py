"""Debug script: tests each protocol command individually to find what works."""

import asyncio
import logging
import sys

from bleak import BleakClient, BleakScanner

sys.path.insert(0, ".")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"
READ_UUID = "0000fa03-0000-1000-8000-00805f9b34fb"
DEVICE_PREFIX = "IDM-"


def notification_handler(sender, data):
    """Log all notifications from the device."""
    logger.info("NOTIFY from %s: %s (hex: %s)", sender, list(data), data.hex())


async def main():
    logger.info("=== iDotMatrix Protocol Debug ===")

    # Step 1: Scan
    logger.info("Scanning for devices...")
    devices = await BleakScanner.discover(timeout=5)
    device = None
    for d in devices:
        if d.name and d.name.startswith(DEVICE_PREFIX):
            device = d
            break

    if not device:
        logger.error("No iDotMatrix device found!")
        return

    logger.info("Found: %s (%s)", device.name, device.address)

    # Step 2: Connect and explore services
    async with BleakClient(device, timeout=10) as client:
        logger.info("Connected!")

        # List all services and characteristics
        logger.info("\n=== BLE Services ===")
        for service in client.services:
            logger.info("Service: %s (%s)", service.uuid, service.description)
            for char in service.characteristics:
                props = ", ".join(char.properties)
                logger.info("  Char: %s [%s] (%s)", char.uuid, props, char.description)

        # Subscribe to notifications
        try:
            await client.start_notify(READ_UUID, notification_handler)
            logger.info("Subscribed to notifications on %s", READ_UUID)
        except Exception as e:
            logger.warning("Could not subscribe to notifications: %s", e)

        await asyncio.sleep(0.5)

        # Test 1: Power ON
        logger.info("\n=== Test 1: Power ON ===")
        cmd = bytearray([5, 0, 7, 1, 1])
        logger.info("Sending: %s (hex: %s)", list(cmd), cmd.hex())
        try:
            await client.write_gatt_char(WRITE_UUID, cmd, response=True)
            logger.info("Write OK (with response)")
        except Exception as e:
            logger.warning("Write with response failed: %s", e)
            try:
                await client.write_gatt_char(WRITE_UUID, cmd, response=False)
                logger.info("Write OK (without response)")
            except Exception as e2:
                logger.error("Write without response also failed: %s", e2)

        await asyncio.sleep(1)

        # Test 2: Brightness 100%
        logger.info("\n=== Test 2: Brightness 100%% ===")
        cmd = bytearray([5, 0, 4, 128, 100])
        logger.info("Sending: %s (hex: %s)", list(cmd), cmd.hex())
        try:
            await client.write_gatt_char(WRITE_UUID, cmd, response=True)
            logger.info("Write OK")
        except Exception as e:
            logger.warning("Failed: %s, trying without response...", e)
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)

        await asyncio.sleep(1)

        # Test 3: Fullscreen color (RED)
        logger.info("\n=== Test 3: Fullscreen RED ===")
        cmd = bytearray([7, 0, 2, 2, 255, 0, 0])
        logger.info("Sending: %s (hex: %s)", list(cmd), cmd.hex())
        try:
            await client.write_gatt_char(WRITE_UUID, cmd, response=True)
            logger.info("Write OK")
        except Exception as e:
            logger.warning("Failed: %s, trying without response...", e)
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)

        await asyncio.sleep(3)
        logger.info("Did the display turn RED? (waiting 3s)")

        # Test 4: Fullscreen GREEN
        logger.info("\n=== Test 4: Fullscreen GREEN ===")
        cmd = bytearray([7, 0, 2, 2, 0, 255, 0])
        logger.info("Sending: %s (hex: %s)", list(cmd), cmd.hex())
        try:
            await client.write_gatt_char(WRITE_UUID, cmd, response=True)
            logger.info("Write OK")
        except Exception as e:
            logger.warning("Failed: %s, trying without response...", e)
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)

        await asyncio.sleep(3)
        logger.info("Did the display turn GREEN?")

        # Test 5: Fullscreen BTC Orange
        logger.info("\n=== Test 5: Fullscreen BTC ORANGE ===")
        cmd = bytearray([7, 0, 2, 2, 255, 153, 0])
        logger.info("Sending: %s (hex: %s)", list(cmd), cmd.hex())
        try:
            await client.write_gatt_char(WRITE_UUID, cmd, response=True)
            logger.info("Write OK")
        except Exception as e:
            logger.warning("Failed: %s, trying without response...", e)
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)

        await asyncio.sleep(3)

        # Test 6: Single pixel (graffiti mode)
        logger.info("\n=== Test 6: Single Pixel at (0,0) WHITE ===")
        # First clear to black
        cmd = bytearray([7, 0, 2, 2, 0, 0, 0])
        await client.write_gatt_char(WRITE_UUID, cmd, response=False)
        await asyncio.sleep(0.5)

        # Set pixel at (0,0) white
        cmd = bytearray([10, 0, 5, 1, 0, 255, 255, 255, 0, 0])
        logger.info("Sending pixel: %s (hex: %s)", list(cmd), cmd.hex())
        try:
            await client.write_gatt_char(WRITE_UUID, cmd, response=True)
            logger.info("Write OK")
        except Exception as e:
            logger.warning("Failed: %s, trying without response...", e)
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)

        await asyncio.sleep(2)
        logger.info("Did a white pixel appear at top-left?")

        # Test 7: Draw a few more pixels to make a pattern
        logger.info("\n=== Test 7: Draw pixel pattern ===")
        pixels = [
            (5, 5, 255, 0, 0),     # red
            (10, 5, 0, 255, 0),     # green
            (15, 5, 0, 0, 255),     # blue
            (5, 10, 255, 255, 0),   # yellow
            (10, 10, 255, 0, 255),  # magenta
            (15, 10, 0, 255, 255),  # cyan
        ]
        for x, y, r, g, b in pixels:
            cmd = bytearray([10, 0, 5, 1, 0, r, g, b, x, y])
            await client.write_gatt_char(WRITE_UUID, cmd, response=False)
            await asyncio.sleep(0.05)

        logger.info("Sent 6 colored pixels. Can you see them?")
        await asyncio.sleep(5)

        # Test 8: Small image upload (32x32 solid orange)
        logger.info("\n=== Test 8: Image upload (32x32 solid orange) ===")
        size = 32
        pixel_count = size * size
        rgb_data = bytes([255, 153, 0] * pixel_count)

        # Try the image header format from protocol docs
        import struct

        total_len = len(rgb_data)
        # Header format: [chunk_len(2), 00 00, flag(1), total_len(4)]
        chunk_data = rgb_data
        header = bytearray(9)
        struct.pack_into("<H", header, 0, len(chunk_data) + 9)  # chunk length including header
        header[2] = 0x00  # command
        header[3] = 0x00  # sub-command
        header[4] = 0x00  # flag: first chunk
        struct.pack_into("<I", header, 5, total_len)  # total data length

        payload = header + chunk_data
        logger.info("Image header: %s (hex: %s)", list(header), header.hex())
        logger.info("Total payload: %d bytes", len(payload))

        # Send in chunks of 512 bytes (MTU safe)
        chunk_size = 512
        for i in range(0, len(payload), chunk_size):
            chunk = payload[i:i + chunk_size]
            try:
                await client.write_gatt_char(WRITE_UUID, chunk, response=False)
            except Exception as e:
                logger.error("Chunk %d failed: %s", i // chunk_size, e)
                break
            await asyncio.sleep(0.02)

        logger.info("Image data sent. Did the display show orange?")
        await asyncio.sleep(5)

        # Stop notifications
        try:
            await client.stop_notify(READ_UUID)
        except Exception:
            pass

        logger.info("\n=== Debug complete ===")
        logger.info("Check which tests produced visible results on the display.")


if __name__ == "__main__":
    asyncio.run(main())
