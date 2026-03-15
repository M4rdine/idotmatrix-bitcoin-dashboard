# idotmatrix-dashboard

> Open-source dashboard for iDotMatrix LED pixel displays via Bluetooth Low Energy (BLE).
> Turn your pixel display into a smart panel with real-time Bitcoin prices, service monitoring, and visual alerts.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)

## What is this?

If you own an iDotMatrix display (those 16x16, 32x32 or 64x64 LED pixel matrices that connect via Bluetooth), this project turns it into a functional dashboard:

- Track Bitcoin price in real-time right on your display
- Monitor the status of your bots, services, or servers with color-coded indicators
- Receive critical visual alerts with full-screen color fills

Runs on anything with Bluetooth -- Raspberry Pi, laptop, desktop.

## Features

- **Bitcoin Ticker** -- Live price from the free CoinGecko API with scrolling animation and 24h change indicator
- **Agent Monitor** -- Service/bot status received via HTTP webhook, displayed as color-coded indicators
- **Alert Mode** -- Full-screen solid color with optional text overlay and blink support
- **Auto Cycling** -- Switches between display modes at a configurable interval
- **Auto Reconnect** -- Automatically attempts to reconnect on BLE connection loss (3 retries)
- **Multi-Resolution** -- Adaptive layout that makes the most of each resolution (16x16, 32x32, 64x64)

## Requirements

- Python 3.11+
- iDotMatrix display (16x16, 32x32, or 64x64)
- Bluetooth Low Energy available on the host (built-in or USB adapter)

## Installation

```bash
# Clone the repository
git clone https://github.com/raphaelmardine/idotmatrix-dashboard.git
cd idotmatrix-dashboard

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

## Configuration

Copy the example file and adjust it to your setup:

```bash
cp .env.example .env
```

The `.env.example` file contains detailed comments explaining every variable. Here's a summary:

### BLE Device

| Variable | Description | Default | Accepted values |
|---|---|---|---|
| `DEVICE_PREFIX` | Bluetooth name prefix of the display | `IDM-` | Any string (check with `led-scan --all`) |
| `DISPLAY_SIZE` | Display resolution in pixels | `32` | `16`, `32`, `64` |
| `BRIGHTNESS` | Display brightness percentage | `80` | `0` to `100` |

### BLE Connection

| Variable | Description | Default | Tip |
|---|---|---|---|
| `BLE_TIMEOUT` | Connection timeout in seconds | `10` | Increase if the device is far away |
| `BLE_SCAN_DURATION` | BLE scan duration in seconds | `5` | Increase for environments with many devices |

### Display Modes

| Variable | Description | Default | Example |
|---|---|---|---|
| `CYCLE_INTERVAL` | Seconds between mode switches | `15` | `30` to switch every 30s |
| `CURRENCIES` | Currencies for BTC price (comma-separated) | `brl,usd` | `usd,eur,gbp,jpy` |

### Webhook & Logging

| Variable | Description | Default | Tip |
|---|---|---|---|
| `WEBHOOK_PORT` | HTTP server port | `8099` | Change if it conflicts with another service |
| `LOG_LEVEL` | Log level | `INFO` | Use `DEBUG` to troubleshoot BLE issues |

## Usage

### Start the dashboard

```bash
led-dashboard
```

Or directly:

```bash
python -m src.main
```

### Scan for BLE devices

Before running the dashboard, check if your display is found:

```bash
led-scan                    # Search for iDotMatrix devices
led-scan --all              # Show ALL BLE devices
led-scan --duration 10      # Scan for 10 seconds
```

### Send agent status via webhook

The webhook server runs automatically alongside the dashboard. Integrate your services by sending updates via POST:

```bash
# Report agent status
curl -X POST http://localhost:8099/api/agents/status \
  -H "Content-Type: application/json" \
  -d '{"name": "trading-bot", "status": "online", "message": "Running smoothly"}'

# List all monitored agents
curl http://localhost:8099/api/agents

# Health check
curl http://localhost:8099/health

# Remove an agent
curl -X DELETE http://localhost:8099/api/agents/trading-bot
```

**Valid statuses:** `online`, `offline`, `error`, `warning`, `degraded`, `running`, `ok`, `unknown`

## Architecture

```
src/
  ble/          # BLE scanner and client (bleak)
  data/         # Data sources (Bitcoin via CoinGecko, agents via webhook)
  modes/        # Display modes (ticker, status, alert)
  protocol/     # iDotMatrix protocol (BLE commands, PNG chunking)
  render/       # Text rendering, colors, and layout composition
  config.py     # Configuration via environment variables (.env)
  main.py       # Main orchestrator (display loop + webhook)
  webhook.py    # FastAPI server for receiving agent status updates
scripts/
  scan.py       # Standalone BLE scanner (CLI)
tests/          # Unit tests
fonts/          # Custom pixel fonts (.ttf)
```

## Tests

```bash
pytest                  # Run tests
pytest --cov=src        # Tests with coverage
pytest -v               # Verbose output
```

## Main Dependencies

| Package | Purpose |
|---|---|
| [bleak](https://github.com/hbldh/bleak) | Bluetooth Low Energy communication |
| [Pillow](https://pillow.readthedocs.io/) | Image rendering for the display |
| [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) | HTTP webhook server |
| [httpx](https://www.python-httpx.org/) | Async HTTP client (CoinGecko API) |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Typed configuration via .env |

## iDotMatrix Protocol

Based on reverse engineering work by:
- [derkalle4/python3-idotmatrix-library](https://github.com/derkalle4/python3-idotmatrix-library)
- [8none1/idotmatrix](https://github.com/8none1/idotmatrix)

Images are sent as PNG files in 4096-byte chunks via BLE GATT.

## Contributing & Roadmap

This is an open-source project and contributions are very welcome! Here are some ideas for where this project can go:

### New Display Modes
- **Clock** -- Show current time with pixel art design
- **Weather** -- Integration with weather APIs (OpenWeatherMap, etc.) for temperature and conditions
- **Notifications** -- Display notifications from GitHub, Telegram, Discord, or other services
- **Sports Scores** -- Live game results
- **Pomodoro** -- Visual timer for the Pomodoro technique
- **Crypto Portfolio** -- Track multiple cryptocurrencies, not just Bitcoin

### Infrastructure Improvements
- **Web UI** -- Browser-based control panel for configuring modes and previewing the display
- **Multi-Display Support** -- Control multiple iDotMatrix devices simultaneously
- **GIFs & Animations** -- Support for uploading and displaying animated GIFs
- **Agent Persistence** -- Save agent status to SQLite instead of in-memory only
- **Docker** -- Ready-to-run container for Raspberry Pi deployment

### Service Integrations
- **Home Assistant** -- Plugin for home automation
- **Prometheus/Grafana** -- Infrastructure metrics and alerts on the display
- **MQTT** -- Integration with IoT systems
- **n8n / Zapier** -- Webhooks for no-code automations

### How to Contribute

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m "feat: description of the feature"`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

## Name Suggestion

The recommended name for this project is **idotmatrix-dashboard**. It's clear, searchable, and immediately tells users what it does. Alternative names to consider:

| Name | Why |
|---|---|
| **idotmatrix-dashboard** | Clear, descriptive, easy to find on GitHub |
| **pixelboard** | Short and catchy, but less specific |
| **dotmatrix-hub** | Emphasizes the hub/central aspect |
| **blematrix** | Highlights BLE + matrix combo |

## License

This project is distributed under the [MIT](LICENSE) license. Use, modify, and distribute freely.
