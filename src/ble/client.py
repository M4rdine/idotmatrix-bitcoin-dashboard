import asyncio
import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from PIL import Image

from src.protocol.commands import (
    WRITE_UUID,
    build_brightness_command,
    build_image_mode_command,
    build_pixel_command,
    build_power_command,
    create_image_payloads,
    pil_image_to_png_bytes,
)


logger = logging.getLogger(__name__)

WRITE_DELAY_SECONDS = 0.01
CHUNK_DELAY_SECONDS = 0.05


class IdmClient:
    """High-level BLE client for iDotMatrix devices."""

    def __init__(self, device: BLEDevice, timeout: float = 10.0) -> None:
        self._device = device
        self._timeout = timeout
        self._client: BleakClient | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def connect(self) -> None:
        logger.info("Connecting to %s (%s)...", self._device.name, self._device.address)
        self._client = BleakClient(self._device, timeout=self._timeout)
        await self._client.connect()
        logger.info("Connected to %s", self._device.name)

    async def disconnect(self) -> None:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            logger.info("Disconnected from %s", self._device.name)
        self._client = None

    async def _write(self, data: bytearray, *, response: bool = True) -> None:
        """Write data to the device, splitting by MTU if needed."""
        if not self._client or not self._client.is_connected:
            raise ConnectionError("Not connected to device")

        char = self._client.services.get_characteristic(WRITE_UUID)
        mtu = char.max_write_without_response_size if char else 512

        for i in range(0, len(data), mtu):
            chunk = data[i:i + mtu]
            await self._client.write_gatt_char(WRITE_UUID, chunk, response=response)

        await asyncio.sleep(WRITE_DELAY_SECONDS)

    async def power_on(self) -> None:
        await self._write(build_power_command(on=True))

    async def power_off(self) -> None:
        await self._write(build_power_command(on=False))

    async def set_brightness(self, percent: int) -> None:
        clamped = max(0, min(100, percent))
        await self._write(build_brightness_command(clamped))

    async def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        await self._write(build_pixel_command(x, y, r, g, b), response=False)

    async def send_image(self, pil_image: Image.Image, size: int) -> None:
        """Convert Pillow image to PNG and upload to display.

        Protocol:
        1. Enter image mode
        2. Send PNG data in chunked payloads (write without response)
        """
        logger.debug("Converting image to PNG and uploading...")

        png_data = pil_image_to_png_bytes(pil_image, size)
        logger.debug("PNG size: %d bytes", len(png_data))

        # Enter image mode
        await self._write(build_image_mode_command(enable=True))
        await asyncio.sleep(0.1)

        # Create and send chunked payloads
        payloads = create_image_payloads(png_data)
        logger.debug("Sending %d payload chunk(s)", len(payloads))

        for i, payload in enumerate(payloads):
            await self._write(payload, response=False)
            if i < len(payloads) - 1:
                await asyncio.sleep(CHUNK_DELAY_SECONDS)

        logger.debug("Image upload complete")

    async def fill_screen_pixels(
        self, image: Image.Image, size: int
    ) -> None:
        """Fallback: draw image pixel-by-pixel using graffiti mode.

        Slower but guaranteed to work since pixel commands are confirmed working.
        """
        if image.size != (size, size):
            image = image.resize((size, size), Image.Resampling.NEAREST)
        if image.mode != "RGB":
            image = image.convert("RGB")

        pixels = image.load()
        for y in range(size):
            for x in range(size):
                r, g, b = pixels[x, y]
                await self.set_pixel(x, y, r, g, b)

    async def __aenter__(self) -> "IdmClient":
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.disconnect()
