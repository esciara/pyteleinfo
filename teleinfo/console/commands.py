import asyncio
import json
import os
import pty
import time

import serial
from cleo import Command

from .utils import _list_ports
from ..exceptions import TeleinfoError
from ..codec import decode
from ..const import ETX, ENCODING
from teleinfo import serial_asyncio

# from teleinfo.console import LOOP


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
            f"Trying to read port '{port}' for {timeout} secs... "
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


import threading


def start_background_loop(loop):
    print("THREAD: starting loop")
    asyncio.set_event_loop(loop)
    loop.run_forever()
    print("THREAD: starting stop_event watch loop")
    # while not stop_event.is_set():
    #     time.sleep(1)
    #     # pass
    # print("THREAD: thread received stop_event.set()")


def start_background_loop_with_event(stop_event, loop):
    print("THREAD: starting loop")
    asyncio.set_event_loop(loop)
    loop.run_forever()
    print("THREAD: starting stop_event watch loop")
    while not stop_event.is_set():
        # time.sleep(1)
        pass
    print("THREAD: thread received stop_event.set()")


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
        # loop = asyncio.get_event_loop()
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)

        # loop.run_until_complete(asyncio.ensure_future(self.async_handle(), loop=loop))
        # loop.close()

        # Give it some async work
        # print("launching async_handle")
        # Create a new loop

        new_loop = asyncio.new_event_loop()

        # pill2kill = threading.Event()

        # Assign the loop to another thread
        t = threading.Thread(target=start_background_loop, args=(new_loop,))
        # t = threading.Thread(target=start_background_loop, args=(pill2kill, new_loop,))
        t.start()
        future = asyncio.run_coroutine_threadsafe(self.async_handle(), new_loop)

        # Wait for the result
        # print("printing result")
        print(future.result())
        future.cancel()
        new_loop.stop()

        # killing the thread
        # pill2kill.set()
        # t.join()

        # ThreadPoolExecutor().submit(new_loop.run_until_complete(asyncio.ensure_future(
        #     self.async_handle()))).result()
        # asyncio.run_coroutine_threadsafe(new_loop.run_until_complete(asyncio.ensure_future(
        #     self.async_handle())), new_loop).result()

        # async def _async_init_from_config_dict(future):
        #     try:
        #         re_hass = await self.async_handle()
        #         future.set_result(re_hass)
        #     # pylint: disable=broad-except
        #     except Exception as exc:
        #         future.set_exception(exc)
        #
        # # run task
        # future = asyncio.Future(loop=loop)
        # loop.create_task(_async_init_from_config_dict(future))
        # loop.run_until_complete(future)

        # self.info("All done!")

    async def async_handle(self):
        port = self.argument("port")
        await self._test_port_for_teleinfo(port, self.option("raw"))
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
                self._test_port_for_teleinfo(port)
            )
            if success:
                self.comment(
                    f"Port {port} receives valid teleinfo frames! Search " f"stopped."
                )
                break

        if not success:
            self.line("All com ports scanned. No port with teleinfo found.")


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
