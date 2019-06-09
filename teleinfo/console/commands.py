import asyncio
import json

import serial
from cleo import Command

from .utils import _list_ports
from ..exceptions import TeleinfoError
from ..codec import decode
from ..const import ETX, ENCODING
from teleinfo import serial_asyncio


class BaseCommand(Command):
    """
    Teleinfo Base Command
    """

    async def _check_port_for_teleinfo(
        self, port, raw_flag=False, max_frames=3, timeout=5.0
    ):
        success = True
        self.info(
            f"Trying to read port '{port}' for {timeout} secs... "
            f"Will print a max of {max_frames} frames..."
        )
        try:
            await _discard_potentially_incomplete_first_frame(port, timeout)
            for i in range(max_frames):
                self.line(await _extract_frame_to_print(port, raw_flag, timeout))
        except serial.SerialException as e:
            self.line_error(f"<error>{e.__repr__()}</>")
            success = False
        except TeleinfoError as e:
            self.line_error(f"<error>{e.__repr__()}</>")
            success = False
        except asyncio.TimeoutError:
            self.comment("Timeout!")
            success = False
        # Add a sleep so that output buffer can be flushed
        await asyncio.sleep(0)
        return success


class PortCommand(BaseCommand):
    """
    Teleinfo port

    port
        {port : Port to listen from}
        {--r|raw : If set, bytes output for the port will be printed instead of
        decoded json}
    """

    def handle(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_handle())

    async def async_handle(self):
        port = self.argument("port")
        await self._check_port_for_teleinfo(port, self.option("raw"))
        # TODO find out how to return an proper exit code


class DiscoveryCommand(BaseCommand):
    """
    Teleinfo Discovery: will try to discover a port that receives teleinfo data

    discover
    """

    def handle(self):
        self.info("Looking for serial ports...")
        ports = _list_ports()
        self.line(f"List of ports found: {ports}")
        self.line(f"Checking port until a teleinfo port is found...")
        success = False
        for port in ports:
            success = asyncio.get_event_loop().run_until_complete(
                self._check_port_for_teleinfo(port)
            )
            if success:
                self.comment(
                    f"Port {port} receives valid teleinfo frames! Search " f"stopped."
                )
                break

        if not success:
            self.line("All com ports scanned. No port with teleinfo found.")


async def _discard_potentially_incomplete_first_frame(port: str, timeout):
    return await asyncio.wait_for(async_receive_frame(port), timeout=timeout)


async def _extract_frame_to_print(port, raw_flag, timeout):
    frame_to_print = await asyncio.wait_for(async_receive_frame(port), timeout=timeout)
    if raw_flag:
        frame_to_print = f"{frame_to_print}"
    else:
        frame_to_print = json.dumps(decode(frame_to_print))
    return frame_to_print


async def async_receive_frame(port: str):
    slave_reader, _ = await serial_asyncio.open_serial_connection(
        url=port,
        baudrate=1200,
        bytesize=serial.SEVENBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        rtscts=1,
    )
    # TODO make sure this stops after a timeout
    return await slave_reader.readuntil(separator=ETX.encode(ENCODING))
