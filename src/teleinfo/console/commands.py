import asyncio
import json
import sys

import termios

import serial_asyncio
from pydantic import BaseModel, Field
from pydantic_settings import CliImplicitFlag, CliPositionalArg
from serial.tools import list_ports

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
        ports_found = list_ports.comports()
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
        await _discard_potentially_incomplete_first_frame(port, settings)
        for _ in range(settings.max_frames):
            print(await _extract_frame_to_print(port, raw_flag, settings))
    except (OSError, termios.error) as exception:
        print(f"Error opening port '{port}': {exception}", file=sys.stderr)
        success = False
    except TeleinfoError as exception:
        print(f"Error: {repr(exception)}", file=sys.stderr)
        success = False
    except asyncio.TimeoutError:
        print("Timeout!")
        success = False
    # Add a sleep so that output buffer can be flushed
    await asyncio.sleep(0)
    return success


async def _discard_potentially_incomplete_first_frame(port: str, settings: TeleinfoSettings):
    return await asyncio.wait_for(async_receive_frame(port, settings), timeout=settings.timeout)


async def _extract_frame_to_print(port: str, raw_flag: bool, settings: TeleinfoSettings) -> str:
    frame_to_print = await asyncio.wait_for(async_receive_frame(port, settings), timeout=settings.timeout)
    if raw_flag:
        return f"{frame_to_print}"
    return json.dumps(decode(frame_to_print))


async def async_receive_frame(port: str, settings: TeleinfoSettings):
    slave_reader, _ = await serial_asyncio.open_serial_connection(
        url=port,
        baudrate=settings.baudrate,
        bytesize=settings.bytesize,
        parity=settings.parity,
        stopbits=settings.stopbits,
        rtscts=settings.rtscts,
    )
    # TODO make sure this stops after a timeout
    return await slave_reader.readuntil(separator=ETX_TOKEN.encode(ENCODING))
