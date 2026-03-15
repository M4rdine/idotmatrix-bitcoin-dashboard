import asyncio
import logging

from bleak import BleakScanner
from bleak.backends.device import BLEDevice


logger = logging.getLogger(__name__)


async def scan_for_device(
    prefix: str = "IDM-",
    scan_duration: float = 5.0,
) -> BLEDevice | None:
    """Scan for an iDotMatrix device by name prefix.

    Returns the first matching device found, or None if no device is found.
    """
    logger.info("Scanning for BLE devices with prefix '%s' for %.1fs...", prefix, scan_duration)

    found_device: BLEDevice | None = None

    def detection_callback(device: BLEDevice, _advertisement_data: object) -> None:
        nonlocal found_device
        if device.name and device.name.startswith(prefix):
            logger.info("Found iDotMatrix device: %s (%s)", device.name, device.address)
            found_device = device

    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    await asyncio.sleep(scan_duration)
    await scanner.stop()

    if found_device is None:
        logger.warning("No iDotMatrix device found during scan")

    return found_device


async def scan_all_devices(
    prefix: str = "IDM-",
    scan_duration: float = 5.0,
) -> list[BLEDevice]:
    """Scan and return all iDotMatrix devices found."""
    logger.info("Scanning for all BLE devices with prefix '%s'...", prefix)

    devices: list[BLEDevice] = []

    def detection_callback(device: BLEDevice, _advertisement_data: object) -> None:
        if device.name and device.name.startswith(prefix):
            if not any(d.address == device.address for d in devices):
                logger.info("Found device: %s (%s)", device.name, device.address)
                devices.append(device)

    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    await asyncio.sleep(scan_duration)
    await scanner.stop()

    logger.info("Found %d iDotMatrix device(s)", len(devices))
    return devices
