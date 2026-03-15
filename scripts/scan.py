"""Standalone BLE scanner script for finding iDotMatrix devices.

Usage:
    python -m scripts.scan
    python -m scripts.scan --prefix IDM- --duration 10
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from bleak import BleakScanner
from bleak.backends.device import BLEDevice


async def scan(prefix: str, duration: float, show_all: bool) -> list[BLEDevice]:
    """Scan for BLE devices and print results."""
    print(f"Scanning for BLE devices for {duration:.0f} seconds...")
    print(f"Filter prefix: '{prefix}'" if not show_all else "Showing ALL devices")
    print("-" * 60)

    found: list[BLEDevice] = []

    def callback(device: BLEDevice, advertisement_data: object) -> None:
        name = device.name or "(unnamed)"

        if show_all or (device.name and device.name.startswith(prefix)):
            if not any(d.address == device.address for d in found):
                found.append(device)
                marker = " <-- iDotMatrix!" if device.name and device.name.startswith(prefix) else ""
                print(f"  [{len(found):2d}] {name:<25s} {device.address}{marker}")

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()

    print("-" * 60)

    idm_devices = [d for d in found if d.name and d.name.startswith(prefix)]
    print(f"Total devices found: {len(found)}")
    print(f"iDotMatrix devices:  {len(idm_devices)}")

    if idm_devices:
        print("\niDotMatrix devices:")
        for device in idm_devices:
            print(f"  Name:    {device.name}")
            print(f"  Address: {device.address}")
            print()

    return idm_devices


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Scan for iDotMatrix BLE devices")
    parser.add_argument(
        "--prefix",
        default="IDM-",
        help="Device name prefix to filter (default: IDM-)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Scan duration in seconds (default: 5)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all",
        help="Show all BLE devices, not just iDotMatrix",
    )
    args = parser.parse_args()

    try:
        asyncio.run(scan(args.prefix, args.duration, args.show_all))
    except KeyboardInterrupt:
        print("\nScan cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
