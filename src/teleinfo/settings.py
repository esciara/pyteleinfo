import serialx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TeleinfoSettings(BaseSettings):
    """Teleinfo serial communication and operational settings."""

    model_config = SettingsConfigDict(env_prefix="TELEINFO_")

    baudrate: int = Field(default=1200, description="Serial baud rate")
    bytesize: int = Field(default=serialx.SEVENBITS, description="Serial byte size")
    parity: str = Field(default=serialx.PARITY_EVEN, description="Serial parity")
    stopbits: int | float = Field(default=serialx.STOPBITS_ONE, description="Serial stop bits")
    rtscts: bool = Field(default=True, description="RTS/CTS flow control")
    max_frames: int = Field(default=3, description="Max frames to read when checking a port")
    timeout: float = Field(default=5.0, description="Read timeout in seconds")
