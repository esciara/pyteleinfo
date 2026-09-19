import asyncio
import json
import sys
import termios

import serialx
from pydantic import BaseModel, Field
from pydantic_settings import CliImplicitFlag, CliPositionalArg

from ..codec import decode
from ..const import ENCODING, ETX_TOKEN
from ..exceptions import TeleinfoError
from ..settings import TeleinfoSettings


class PortCommand(BaseModel):
    """Read teleinfo frames from a specific serial port."""

    port: CliPositionalArg[str]
    raw: CliImplicitFlag[bool] = Field(default=False, description="Print raw bytes instead of decoded JSON")

    async def cli_cmd(self) -> None:
        settings = TeleinfoSettings()
        await _check_port_for_teleinfo(self.port, settings, raw_flag=self.raw)


class DiscoverCommand(BaseModel):
    """Auto-discover a serial port receiving teleinfo data."""

    async def cli_cmd(self) -> None:
        settings = TeleinfoSettings()
        print("Looking for serial ports...")
        ports_found = await serialx.async_list_serial_ports()
        ports = [port.device for port in ports_found]
        print(f"List of ports found: {ports}")
        print("Checking port until a teleinfo port is found...")
        success = False
        for port in ports:
            success = await _check_port_for_teleinfo(port, settings)
            if success:
                print(f"Port {port} receives valid teleinfo frames! Search stopped.")
                break

        if not success:
            print("All com ports scanned. No port with teleinfo found.")


async def _check_port_for_teleinfo(port: str, settings: TeleinfoSettings, raw_flag: bool = False) -> bool:
    success = True
    print(
        f"Trying to read port '{port}' for {settings.timeout} secs... Will print a max of {settings.max_frames} frames..."
    )
    try:
        async with _open_port(port, settings) as ser:
            # The first frame read after opening is most likely incomplete: discard it.
            await async_receive_frame(ser, settings.timeout)
            for _ in range(settings.max_frames):
                frame = await async_receive_frame(ser, settings.timeout)
                print(f"{frame!r}" if raw_flag else json.dumps(decode(frame)))
    except TimeoutError:
        # Must come before OSError: TimeoutError is a subclass of it.
        print("Timeout!")
        success = False
    except (OSError, termios.error, asyncio.IncompleteReadError) as exception:
        print(f"Error reading port '{port}': {exception}", file=sys.stderr)
        success = False
    except TeleinfoError as exception:
        print(f"Error: {repr(exception)}", file=sys.stderr)
        success = False
    # Add a sleep so that output buffer can be flushed
    await asyncio.sleep(0)
    return success


def _open_port(port: str, settings: TeleinfoSettings) -> serialx.AsyncSerial:
    """Build an unopened async serial port configured from *settings*."""
    return serialx.async_serial_for_url(
        port,
        baudrate=settings.baudrate,
        byte_size=settings.bytesize,
        parity=settings.parity,
        stopbits=settings.stopbits,
        rtscts=settings.rtscts,
    )


async def async_receive_frame(ser: serialx.AsyncSerial, timeout: float) -> bytes:
    """Read from *ser* up to and including the next ETX, giving up after *timeout* seconds.

    Raises:
        TimeoutError: No ETX received within *timeout* seconds.
        asyncio.IncompleteReadError: The port closed before an ETX was received.
    """
    return await asyncio.wait_for(ser.readuntil(ETX_TOKEN.encode(ENCODING)), timeout=timeout)
