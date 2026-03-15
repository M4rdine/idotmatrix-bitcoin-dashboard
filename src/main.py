"""Main entry point for the LED Matrix Dashboard.

Orchestrates:
1. BLE device scanning and connection
2. Webhook server startup (background thread)
3. Mode cycling loop (ticker -> status -> ticker -> ...)
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import threading
from dataclasses import dataclass, field

import uvicorn

from src.ble.client import IdmClient
from src.ble.scanner import scan_for_device
from src.config import Settings, get_settings
from src.modes.alert import AlertMode
from src.modes.status import StatusMode
from src.modes.ticker import TickerMode


logger = logging.getLogger(__name__)


@dataclass
class DisplayMode:
    """Wraps a mode with its metadata."""

    instance: TickerMode | StatusMode | AlertMode
    name: str
    data_refresh_interval: int = 60  # seconds
    _last_refresh: float = 0.0


@dataclass
class Dashboard:
    """Main dashboard controller.

    Manages the display loop, mode cycling, and BLE connection.
    """

    settings: Settings
    _modes: list[DisplayMode] = field(default_factory=list)
    _current_mode_index: int = 0
    _running: bool = False
    _client: IdmClient | None = None

    def __post_init__(self) -> None:
        size = self.settings.display_size
        currencies = self.settings.currency_list

        self._modes = [
            DisplayMode(
                instance=TickerMode(size=size, currencies=currencies),
                name="ticker",
                data_refresh_interval=60,
            ),
            DisplayMode(
                instance=StatusMode(size=size),
                name="status",
                data_refresh_interval=10,
            ),
        ]

    @property
    def current_mode(self) -> DisplayMode:
        return self._modes[self._current_mode_index]

    def next_mode(self) -> DisplayMode:
        """Advance to the next display mode (immutable index update)."""
        self._current_mode_index = (self._current_mode_index + 1) % len(self._modes)
        logger.info("Switched to mode: %s", self.current_mode.name)
        return self.current_mode

    async def connect(self) -> bool:
        """Scan for and connect to an iDotMatrix device."""
        device = await scan_for_device(
            prefix=self.settings.device_prefix,
            scan_duration=self.settings.ble_scan_duration,
        )
        if device is None:
            logger.error("No iDotMatrix device found")
            return False

        self._client = IdmClient(device, timeout=self.settings.ble_timeout)
        try:
            await self._client.connect()
            await self._client.power_on()
            await self._client.set_brightness(self.settings.brightness)
            return True
        except Exception as exc:
            logger.error("Failed to connect: %s", exc)
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as exc:
                logger.warning("Error during disconnect: %s", exc)
            self._client = None

    async def run_loop(self) -> None:
        """Main display loop: cycle modes and send frames."""
        self._running = True
        cycle_interval = self.settings.cycle_interval
        frame_interval = 0.5  # seconds between frame renders

        logger.info(
            "Starting display loop (cycle: %ds, size: %d)",
            cycle_interval,
            self.settings.display_size,
        )

        mode_timer = 0.0

        while self._running:
            try:
                mode = self.current_mode

                # Refresh data if needed
                elapsed = asyncio.get_event_loop().time() - mode._last_refresh
                if elapsed >= mode.data_refresh_interval or mode._last_refresh == 0.0:
                    await mode.instance.update_data()
                    mode._last_refresh = asyncio.get_event_loop().time()

                # Render frame
                frame = mode.instance.render()

                # Send to device
                if self._client and self._client.is_connected:
                    try:
                        await self._client.send_image(frame, self.settings.display_size)
                    except Exception as exc:
                        logger.error("Failed to send frame: %s", exc)
                        await self._handle_connection_error()

                # Check mode cycle timer
                mode_timer += frame_interval
                if mode_timer >= cycle_interval:
                    self.next_mode()
                    mode_timer = 0.0

                await asyncio.sleep(frame_interval)

            except asyncio.CancelledError:
                logger.info("Display loop cancelled")
                break
            except Exception as exc:
                logger.error("Display loop error: %s", exc)
                await asyncio.sleep(1.0)

    async def _handle_connection_error(self) -> None:
        """Attempt to reconnect after a connection error."""
        logger.warning("Connection lost, attempting to reconnect...")
        await self.disconnect()
        await asyncio.sleep(2.0)

        for attempt in range(3):
            logger.info("Reconnection attempt %d/3", attempt + 1)
            if await self.connect():
                logger.info("Reconnected successfully")
                return
            await asyncio.sleep(2.0)

        logger.error("Failed to reconnect after 3 attempts")

    def stop(self) -> None:
        """Signal the display loop to stop."""
        self._running = False
        logger.info("Dashboard stop requested")


def start_webhook_server(port: int) -> threading.Thread:
    """Start the webhook server in a background thread.

    Returns the thread so it can be joined on shutdown.
    """
    from src.webhook import app

    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(
        target=server.run,
        daemon=True,
        name="webhook-server",
    )
    thread.start()
    logger.info("Webhook server started on port %d", port)
    return thread


async def async_main() -> None:
    """Async entry point."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("LED Matrix Dashboard starting...")
    logger.info("Display size: %dx%d", settings.display_size, settings.display_size)
    logger.info("Cycle interval: %ds", settings.cycle_interval)

    # Start webhook server
    start_webhook_server(settings.webhook_port)

    # Create dashboard
    dashboard = Dashboard(settings=settings)

    # Handle graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler() -> None:
        logger.info("Shutdown signal received")
        dashboard.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Connect to device
    connected = await dashboard.connect()
    if not connected:
        logger.warning("Running without device connection (display output disabled)")

    # Run display loop
    try:
        await dashboard.run_loop()
    finally:
        await dashboard.disconnect()
        logger.info("Dashboard shutdown complete")


def run() -> None:
    """Synchronous entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(0)


if __name__ == "__main__":
    run()
