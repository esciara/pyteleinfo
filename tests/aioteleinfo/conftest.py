# content of conftest.py
import os
import pty
import asyncio

import pytest

from teleinfo.const import *
from teleinfo.codec import encode_info_group

VALID_FRAME_DATA = [{LABEL: 'ADCO', DATA: '050022120078', CHECKSUM: '2'},
                    {LABEL: 'OPTARIF', DATA: 'HC..', CHECKSUM: '<'},
                    {LABEL: 'ISOUSC', DATA: '45', CHECKSUM: '?'},
                    {LABEL: 'HCHC', DATA: '094939439', CHECKSUM: '8'},
                    {LABEL: 'HCHP', DATA: '127970334', CHECKSUM: '7'},
                    {LABEL: 'PTEC', DATA: 'HP..', CHECKSUM: ' '},
                    {LABEL: 'IINST', DATA: '009', CHECKSUM: ' '},
                    {LABEL: 'IMAX', DATA: '049', CHECKSUM: 'L'},
                    {LABEL: 'PAPP', DATA: '02160', CHECKSUM: '*'},
                    {LABEL: 'HHPHC', DATA: 'E', CHECKSUM: '0'},
                    {LABEL: 'MOTDETAT', DATA: '400000', CHECKSUM: 'F'}]

VALID_FRAME = b'\x02' \
              b'\nADCO 050022120078 2\r' \
              b'\nOPTARIF HC.. <\r' \
              b'\nISOUSC 45 ?\r' \
              b'\nHCHC 094939439 8\r' \
              b'\nHCHP 127970334 7\r' \
              b'\nPTEC HP..  \r' \
              b'\nIINST 009  \r' \
              b'\nIMAX 049 L\r' \
              b'\nPAPP 02160 *\r' \
              b'\nHHPHC E 0\r' \
              b'\nMOTDETAT 400000 F\r' \
              b'\x03'

VALID_FRAME_JSON = {'ADCO': '050022120078',
                    'OPTARIF': 'HC..',
                    'ISOUSC': '45',
                    'HCHC': '094939439',
                    'HCHP': '127970334',
                    'PTEC': 'HP..',
                    'IINST': '009',
                    'IMAX': '049',
                    'PAPP': '02160',
                    'HHPHC': 'E',
                    'MOTDETAT': '400000'}


def _build_valid_frame_json(data: list):
    json_ = {}
    for item in data:
        json_[item[LABEL]] = item[DATA]
    return json_


def _build_frame(data: list):
    frame = STX
    for item in data:
        frame = ''.join([frame,
                         encode_info_group(item[LABEL], item[DATA])])
    frame = ''.join([frame,
                     ETX])
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


@pytest.fixture
async def slave_name():
    master, slave = pty.openpty()  # open the pseudoterminal
    slave_name = os.ttyname(slave)
    # valid_frame = _build_frame(VALID_FRAME_DATA)
    # print('valid_frame sent: {}'.format(valid_frame))
    # print('valid_frame sent (bytes version): {}'.format(valid_frame.encode()))
    # print('valid_frame sent (ascii version): {}'.format(valid_frame.encode('ascii')))
    # send_task: asyncio.Future = asyncio.ensure_future(send_data(master, VALID_FRAME_DATA))
    send_task: asyncio.Future = asyncio.ensure_future(send(master, VALID_FRAME))
    # send_task: asyncio.Future = asyncio.ensure_future(send(master, valid_frame))
    yield slave_name
    send_task.cancel()


async def send(master, valid_frame):
    while True:
        os.write(master, valid_frame)
        await asyncio.sleep(0)
