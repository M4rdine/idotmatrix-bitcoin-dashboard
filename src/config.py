from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    device_prefix: str = "IDM-"
    display_size: int = 32
    brightness: int = 80
    cycle_interval: int = 15
    currencies: str = "brl,usd"
    webhook_port: int = 8099
    ble_timeout: int = 10
    ble_scan_duration: int = 5
    log_level: str = "INFO"

    @property
    def currency_list(self) -> list[str]:
        return [c.strip().lower() for c in self.currencies.split(",")]

    @property
    def resolution(self) -> tuple[int, int]:
        return (self.display_size, self.display_size)


def get_settings() -> Settings:
    return Settings()
