"""Tests for teleinfo.console.commands (async port checking)."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
import serialx
from hamcrest import assert_that, equal_to, is_

from teleinfo.console.commands import _check_port_for_teleinfo, async_receive_frame
from teleinfo.settings import TeleinfoSettings


FRAME_1 = b"\x02\nADCO 050022120078 2\r\x03"
FRAME_2 = b"\x02\nADCO 050022120079 3\r\x03"
PARTIAL_FRAME = b"\nADCO 050022120078 2\r\x03"


@pytest.fixture
def mock_port(mocker):
    """Patch serialx.async_serial_for_url with an async context manager yielding a fake port."""
    mock_factory = mocker.patch("teleinfo.console.commands.serialx.async_serial_for_url")
    mock_ser = MagicMock()
    mock_ser.readuntil = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_ser)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_factory, mock_ser


@pytest.mark.asyncio
async def test_check_port_opens_once_and_discards_first_frame(mock_port, capsys):
    mock_factory, mock_ser = mock_port
    mock_ser.readuntil.side_effect = [PARTIAL_FRAME, FRAME_1, FRAME_2]
    settings = TeleinfoSettings(max_frames=2)

    success = await _check_port_for_teleinfo("/dev/ttyUSB0", settings)

    assert_that(success, is_(True))
    mock_factory.assert_called_once_with(
        "/dev/ttyUSB0",
        baudrate=1200,
        byte_size=serialx.SEVENBITS,
        parity=serialx.PARITY_EVEN,
        stopbits=serialx.STOPBITS_ONE,
        rtscts=True,
    )
    assert_that(mock_ser.readuntil.await_count, equal_to(3))
    printed = capsys.readouterr().out.splitlines()
    assert_that(printed[-2:], equal_to([json.dumps({"ADCO": "050022120078"}), json.dumps({"ADCO": "050022120079"})]))


@pytest.mark.asyncio
async def test_check_port_prints_raw_frames(mock_port, capsys):
    _, mock_ser = mock_port
    mock_ser.readuntil.side_effect = [PARTIAL_FRAME, FRAME_1]
    settings = TeleinfoSettings(max_frames=1)

    await _check_port_for_teleinfo("/dev/ttyUSB0", settings, raw_flag=True)

    assert_that(capsys.readouterr().out.splitlines()[-1], equal_to(f"{FRAME_1!r}"))


@pytest.mark.asyncio
async def test_check_port_reports_missing_device(mock_port, capsys):
    mock_factory, _ = mock_port
    mock_factory.return_value.__aenter__.side_effect = FileNotFoundError(2, "No such file or directory")

    success = await _check_port_for_teleinfo("/dev/ttyNOPE", settings=TeleinfoSettings())

    assert_that(success, is_(False))
    assert_that("Error reading port '/dev/ttyNOPE'" in capsys.readouterr().err, is_(True))


@pytest.mark.asyncio
async def test_check_port_reports_timeout(mock_port, capsys):
    _, mock_ser = mock_port
    mock_ser.readuntil.side_effect = TimeoutError()

    success = await _check_port_for_teleinfo("/dev/ttyUSB0", settings=TeleinfoSettings())

    assert_that(success, is_(False))
    assert_that("Timeout!" in capsys.readouterr().out, is_(True))


@pytest.mark.asyncio
async def test_check_port_reports_port_closed_mid_frame(mock_port, capsys):
    _, mock_ser = mock_port
    mock_ser.readuntil.side_effect = asyncio.IncompleteReadError(b"\x02partial", None)

    success = await _check_port_for_teleinfo("/dev/ttyUSB0", settings=TeleinfoSettings())

    assert_that(success, is_(False))
    assert_that("Error reading port" in capsys.readouterr().err, is_(True))


@pytest.mark.asyncio
async def test_check_port_reports_invalid_frame(mock_port, capsys):
    _, mock_ser = mock_port
    mock_ser.readuntil.side_effect = [PARTIAL_FRAME, b"\x02\nADCO 050022120078 X\r\x03"]

    success = await _check_port_for_teleinfo("/dev/ttyUSB0", settings=TeleinfoSettings(max_frames=1))

    assert_that(success, is_(False))
    assert_that(capsys.readouterr().err.startswith("Error: "), is_(True))


@pytest.mark.asyncio
async def test_async_receive_frame_times_out():
    ser = MagicMock()

    async def never_returns(_separator):
        await asyncio.sleep(10)

    ser.readuntil = never_returns

    with pytest.raises(TimeoutError):
        await async_receive_frame(ser, timeout=0.01)
