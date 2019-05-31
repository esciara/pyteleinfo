import asyncio
import json
import os
import pty
import sys

import serial
from cleo import Command

from ..exceptions import TeleinfoError
from ..codec import decode
from ..const import ETX, ENCODING
from teleinfo import serial_asyncio

VALID_FRAME = (
    b"\x02"
    b"\nADCO 050022120078 2\r"
    b"\nOPTARIF HC.. <\r"
    b"\nISOUSC 45 ?\r"
    b"\nHCHC 094939439 8\r"
    b"\nHCHP 127970334 7\r"
    b"\nPTEC HP..  \r"
    b"\nIINST 009  \r"
    b"\nIMAX 049 L\r"
    b"\nPAPP 02160 *\r"
    b"\nHHPHC E 0\r"
    b"\nMOTDETAT 400000 F\r"
    b"\x03"
)


class BaseCommand(Command):
    """
    Teleinfo Base Command
    """

    async def _test_port_for_teleinfo(
        self, port, raw_flag=False, max_frames=3, timeout=5.0
    ):
        success = True
        self.info(
            f"Trying to ready port '{port}' for {timeout} secs... "
            f"Will print a max of {max_frames} frames..."
        )
        try:
            for i in range(max_frames):
                frame = await asyncio.wait_for(
                    asyncio.ensure_future(async_receive_frame(port)), timeout=timeout
                )
                if raw_flag:
                    print(frame)
                else:
                    frame_json = json.dumps(decode(frame))
                    self.line(frame_json)
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
        self.info("Starting the loop...")
        asyncio.get_event_loop().run_until_complete(self.async_handle())
        self.info("All done!")

    async def async_handle(self):
        port = self.argument("port")

        master, slave = pty.openpty()  # open the pseudoterminal
        slave_name_ = os.ttyname(slave)
        send_task = asyncio.ensure_future(send(master, VALID_FRAME))

        port = slave_name_
        await self._test_port_for_teleinfo(port, self.option("raw"))

        send_task.cancel()


class DiscoveryCommand(BaseCommand):
    """
    Teleinfo Discovery: will try to discover a port that receives teleinfo data

    discover
    """

    def handle(self):
        self.info("Looking for serial ports...")

        master, slave = pty.openpty()  # open the pseudoterminal
        slave_name_ = os.ttyname(slave)
        send_task = asyncio.ensure_future(send(master, VALID_FRAME))

        ports = _list_ports()

        ports.append(slave_name_)

        self.line(f"List of ports found: {ports}")

        success = False
        for port in ports:
            success = asyncio.get_event_loop().run_until_complete(
                self._test_port_for_teleinfo(port)
            )
            if success:
                self.comment(
                    f"Port {port} receives valid teleinfo frames! Search " f"stopped."
                )
                break

        if not success:
            self.line("All com ports scanned. No port with teleinfo found.")

        send_task.cancel()


def _list_ports():
    import subprocess

    proc = subprocess.Popen(
        ["python -m serial.tools.list_ports"], stdout=subprocess.PIPE, shell=True
    )
    (out, _) = proc.communicate()
    import io

    buf = io.StringIO(out.decode("ascii"))
    lines = buf.read().splitlines()
    return lines


async def send(master, valid_frame):
    while True:
        os.write(master, valid_frame)
        await asyncio.sleep(0)


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
