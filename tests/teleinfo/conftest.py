# pylint: disable=missing-docstring
import os
import pty
import threading

import pytest
import pytest_asyncio

from teleinfo.codec import encode_info_group
from teleinfo.const import CHECKSUM_KEY, DATA_KEY, ETX_TOKEN, LABEL_KEY, STX_TOKEN

VALID_FRAME_DATA = [
    {LABEL_KEY: "ADCO", DATA_KEY: "050022120078", CHECKSUM_KEY: "2"},
    {LABEL_KEY: "OPTARIF", DATA_KEY: "HC..", CHECKSUM_KEY: "<"},
    {LABEL_KEY: "ISOUSC", DATA_KEY: "45", CHECKSUM_KEY: "?"},
    {LABEL_KEY: "HCHC", DATA_KEY: "094939439", CHECKSUM_KEY: "8"},
    {LABEL_KEY: "HCHP", DATA_KEY: "127970334", CHECKSUM_KEY: "7"},
    {LABEL_KEY: "PTEC", DATA_KEY: "HP..", CHECKSUM_KEY: " "},
    {LABEL_KEY: "IINST", DATA_KEY: "009", CHECKSUM_KEY: " "},
    {LABEL_KEY: "IMAX", DATA_KEY: "049", CHECKSUM_KEY: "L"},
    {LABEL_KEY: "PAPP", DATA_KEY: "02160", CHECKSUM_KEY: "*"},
    {LABEL_KEY: "HHPHC", DATA_KEY: "E", CHECKSUM_KEY: "0"},
    {LABEL_KEY: "MOTDETAT", DATA_KEY: "400000", CHECKSUM_KEY: "F"},
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
        json_[item[LABEL_KEY]] = item[DATA_KEY]
    return json_


def _build_frame(data: list):
    frame = STX_TOKEN
    for item in data:
        frame = "".join([frame, encode_info_group(item[LABEL_KEY], item[DATA_KEY])])
    frame = "".join([frame, ETX_TOKEN])
    return frame


@pytest_asyncio.fixture
async def valid_frame():
    yield VALID_FRAME


@pytest_asyncio.fixture
async def valid_frame_data():
    yield VALID_FRAME_DATA


@pytest_asyncio.fixture
async def valid_frame_json():
    yield VALID_FRAME_JSON


class OsWriteThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, master, frame, first_frame_dirty=False):
        super().__init__()
        self._stop_event = threading.Event()
        self.master = master
        self.frame = frame
        self.first_frame_dirty = first_frame_dirty

    def run(self):
        if self.first_frame_dirty:
            os.write(self.master, self.frame[5:])
        while not self._stop_event.isSet():
            os.write(self.master, self.frame)
            self._stop_event.wait(0.1)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


@pytest.fixture
def slave():
    yield from slave_dirty_or_not(False)


@pytest.fixture
def slave_with_dirty_first_frame():
    yield from slave_dirty_or_not(True)


def slave_dirty_or_not(first_frame_dirty):
    master, slave = pty.openpty()  # open the pseudoterminal
    slave_name_ = os.ttyname(slave)
    thread = OsWriteThread(master, VALID_FRAME, first_frame_dirty)
    thread.start()
    yield slave_name_
    thread.stop()
