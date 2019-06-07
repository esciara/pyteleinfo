# pylint: disable=missing-docstring
import asyncio
import os
import pty
from asyncio import CancelledError

import pytest

from teleinfo.codec import encode_info_group
from teleinfo.const import CHECKSUM, DATA, ETX, LABEL, STX

# import nest_asyncio
#
# # Fixes issues with running pytest.asyncio and having a
# # “RuntimeError: This event loop is already running” when doing a
# # asyncio.get_event_loop().run_until_complete(...)
# # (see https://github.com/spyder-ide/spyder/issues/7096#issuecomment-449655308)
# nest_asyncio.apply()


VALID_FRAME_DATA = [
    {LABEL: "ADCO", DATA: "050022120078", CHECKSUM: "2"},
    {LABEL: "OPTARIF", DATA: "HC..", CHECKSUM: "<"},
    {LABEL: "ISOUSC", DATA: "45", CHECKSUM: "?"},
    {LABEL: "HCHC", DATA: "094939439", CHECKSUM: "8"},
    {LABEL: "HCHP", DATA: "127970334", CHECKSUM: "7"},
    {LABEL: "PTEC", DATA: "HP..", CHECKSUM: " "},
    {LABEL: "IINST", DATA: "009", CHECKSUM: " "},
    {LABEL: "IMAX", DATA: "049", CHECKSUM: "L"},
    {LABEL: "PAPP", DATA: "02160", CHECKSUM: "*"},
    {LABEL: "HHPHC", DATA: "E", CHECKSUM: "0"},
    {LABEL: "MOTDETAT", DATA: "400000", CHECKSUM: "F"},
]

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

VALID_FRAME_JSON = {
    "ADCO": "050022120078",
    "OPTARIF": "HC..",
    "ISOUSC": "45",
    "HCHC": "094939439",
    "HCHP": "127970334",
    "PTEC": "HP..",
    "IINST": "009",
    "IMAX": "049",
    "PAPP": "02160",
    "HHPHC": "E",
    "MOTDETAT": "400000",
}


def _build_valid_frame_json(data: list):
    json_ = {}
    for item in data:
        json_[item[LABEL]] = item[DATA]
    return json_


def _build_frame(data: list):
    frame = STX
    for item in data:
        frame = "".join([frame, encode_info_group(item[LABEL], item[DATA])])
    frame = "".join([frame, ETX])
    return frame


@pytest.fixture
async def valid_frame():
    yield VALID_FRAME


@pytest.fixture
async def valid_frame_data():
    yield VALID_FRAME_DATA


@pytest.fixture
async def valid_frame_json():
    yield VALID_FRAME_JSON


from threading import Thread


def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


@pytest.fixture
async def slave_name():
    master, slave = pty.openpty()  # open the pseudoterminal
    slave_name_ = os.ttyname(slave)
    # valid_frame = _build_frame(VALID_FRAME_DATA)
    # print('valid_frame sent: {}'.format(valid_frame))
    # print('valid_frame sent (bytes version): {}'.format(valid_frame.encode()))
    # print('valid_frame sent (ascii version): {}'.format(valid_frame.encode('ascii')))
    # send_task: asyncio.Future = asyncio.ensure_future(send_data(master,
    # VALID_FRAME_DATA))
    # Create a new loop
    fixture_loop = asyncio.new_event_loop()

    # Assign the loop to another thread
    Thread(target=start_background_loop, args=(fixture_loop,)).start()
    print("FIXTURE: sending task")
    send_task = asyncio.run_coroutine_threadsafe(
        send(master, VALID_FRAME), fixture_loop
    )
    # send_task = asyncio.ensure_future(send(master, VALID_FRAME))
    # send_task: asyncio.Future = asyncio.ensure_future(send(master, valid_frame))
    print("FIXTURE: task sent. yielding")
    yield slave_name_
    print("FIXTURE: cancelling send task")
    try:
        send_task.cancel()
    except CancelledError:
        pass
    fixture_loop.stop()


# pylint: disable=redefined-outer-name
async def send(master, valid_frame):
    while True:
        os.write(master, valid_frame)
        await asyncio.sleep(0)
