"""Synchronous Teleinfo serial frame reader."""

from __future__ import annotations

import time

import serial

from .const import ENCODING, ETX_TOKEN, STX_TOKEN
from .settings import TeleinfoSettings


def read_frame(port: str, settings: TeleinfoSettings | None = None) -> bytes:
    """Open *port* and read one complete Teleinfo frame synchronously.

    Bytes before STX are silently discarded. Enforces an overall deadline
    to prevent blocking indefinitely.

    Args:
        port: Serial device path (e.g. ``"/dev/ttyUSB0"``).
        settings: Serial and timeout configuration. Defaults to
            :class:`~teleinfo.settings.TeleinfoSettings` when ``None``.

    Returns:
        Raw frame bytes from STX through ETX (inclusive).

    Raises:
        TimeoutError: Deadline exceeded waiting for STX/ETX, or no data received.
        serial.SerialException: Port-open or I/O failures (propagated directly).
    """
    if settings is None:
        settings = TeleinfoSettings()

    stx = STX_TOKEN.encode(ENCODING)
    etx = ETX_TOKEN.encode(ENCODING)
    deadline = time.monotonic() + settings.timeout

    with serial.Serial(
        port=port,
        baudrate=settings.baudrate,
        bytesize=settings.bytesize,
        parity=settings.parity,
        stopbits=settings.stopbits,
        rtscts=settings.rtscts,
        timeout=settings.timeout,
    ) as ser:
        # Read until we find STX (start of frame)
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Overall timeout waiting for STX")
            byte = ser.read(1)
            if not byte:
                raise TimeoutError("No data received from serial port")
            if byte == stx:
                break

        # Read until ETX (end of frame)
        frame = bytearray(stx)
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Overall timeout waiting for ETX")
            byte = ser.read(1)
            if not byte:
                raise TimeoutError("Incomplete frame: no ETX received")
            frame.append(byte[0])
            if byte == etx:
                break

    return bytes(frame)
