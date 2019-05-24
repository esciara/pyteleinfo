# pylint: disable=missing-docstring

import pytest
import serial
from hamcrest import assert_that, equal_to

from teleinfo import serial_asyncio
from teleinfo.codec import decode
from teleinfo.const import ENCODING, ETX


@pytest.mark.asyncio
async def test_receive_and_decode_teleinfo(slave_name, valid_frame_json):
    # test whether the app correctly adds contract number to
    # Given I receive a valid frame
    frame = await receive_frame(slave_name)

    # When I decode the frame
    frame_json = decode(frame)

    # Then the decoded frame should be the valid json data
    expected = valid_frame_json

    assert_that(
        frame_json,
        equal_to(expected),
        "Received frame should have been properly decoded",
    )


async def receive_frame(slave_name: str):
    slave_reader, _ = await serial_asyncio.open_serial_connection(
        url=slave_name,
        baudrate=1200,
        bytesize=serial.SEVENBITS,
        #   parity=serial.PARITY_EVEN,  => changed to test on debian flavors
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        rtscts=1,
    )
    return await slave_reader.readuntil(separator=ETX.encode(ENCODING))
