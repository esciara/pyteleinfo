"""Tests for teleinfo.serial_reader."""

from unittest.mock import MagicMock

import pytest
import serial
from hamcrest import assert_that, equal_to

from teleinfo.serial_reader import read_frame
from teleinfo.settings import TeleinfoSettings


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_serial(mocker):
    """Patch serial.Serial and return (mock_cls, mock_ser_instance)."""
    mock_cls = mocker.patch("teleinfo.serial_reader.serial.Serial")
    mock_ser = MagicMock()
    mock_cls.return_value.__enter__.return_value = mock_ser
    mock_cls.return_value.__exit__.return_value = False
    return mock_cls, mock_ser


@pytest.fixture
def frozen_time(mocker):
    """Return a controllable monotonic clock."""
    return mocker.patch("teleinfo.serial_reader.time.monotonic")


# ── helpers ─────────────────────────────────────────────────────────────────


def _bytes_to_reads(data: bytes) -> list[bytes]:
    """Convert a bytes object to a list of single-byte read results."""
    return [bytes([b]) for b in data]


MINIMAL_FRAME = b"\x02\nADCO 050022120078 2\r\x03"


# ── happy path ──────────────────────────────────────────────────────────────


def test_read_frame_returns_complete_frame(mock_serial):
    _, mock_ser = mock_serial
    # Two junk bytes before STX, then the frame
    mock_ser.read.side_effect = [b"\x01", b"\xff"] + _bytes_to_reads(MINIMAL_FRAME)

    result = read_frame("/dev/ttyUSB0")

    assert_that(result, equal_to(MINIMAL_FRAME))


def test_read_frame_uses_default_settings(mock_serial):
    mock_cls, mock_ser = mock_serial
    mock_ser.read.side_effect = _bytes_to_reads(MINIMAL_FRAME)

    read_frame("/dev/ttyUSB0")

    mock_cls.assert_called_once_with(
        port="/dev/ttyUSB0",
        baudrate=1200,
        bytesize=serial.SEVENBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        rtscts=1,
        timeout=5.0,
    )


def test_read_frame_uses_custom_settings(mock_serial):
    mock_cls, mock_ser = mock_serial
    mock_ser.read.side_effect = _bytes_to_reads(MINIMAL_FRAME)
    settings = TeleinfoSettings(timeout=10.0)

    read_frame("/dev/ttyUSB0", settings=settings)

    _, kwargs = mock_cls.call_args
    assert_that(kwargs["timeout"], equal_to(10.0))


# ── timeout cases ───────────────────────────────────────────────────────────


def test_read_frame_raises_timeout_waiting_for_stx(mock_serial, frozen_time):
    _, mock_ser = mock_serial
    # monotonic: t0=0 (for deadline calc), then t0+6 (past 5s deadline)
    frozen_time.side_effect = [0.0, 6.0]
    mock_ser.read.side_effect = [b"\x01"]

    with pytest.raises(TimeoutError, match="Overall timeout waiting for STX"):
        read_frame("/dev/ttyUSB0")


def test_read_frame_raises_timeout_waiting_for_etx(mock_serial, frozen_time):
    _, mock_ser = mock_serial
    # t0=0 (deadline=5), t0+0.1 (STX check passes), t0+6 (past deadline)
    frozen_time.side_effect = [0.0, 0.1, 6.0]
    mock_ser.read.side_effect = [b"\x02", b"\n"]

    with pytest.raises(TimeoutError, match="Overall timeout waiting for ETX"):
        read_frame("/dev/ttyUSB0")


# ── no-data cases ──────────────────────────────────────────────────────────


def test_read_frame_raises_timeout_on_empty_read_before_stx(mock_serial):
    _, mock_ser = mock_serial
    mock_ser.read.return_value = b""

    with pytest.raises(TimeoutError, match="No data received from serial port"):
        read_frame("/dev/ttyUSB0")


def test_read_frame_raises_timeout_on_empty_read_after_stx(mock_serial):
    _, mock_ser = mock_serial
    mock_ser.read.side_effect = [b"\x02", b""]

    with pytest.raises(TimeoutError, match="Incomplete frame: no ETX received"):
        read_frame("/dev/ttyUSB0")


# ── serial exception propagation ───────────────────────────────────────────


def test_read_frame_propagates_serial_exception(mocker):
    mocker.patch(
        "teleinfo.serial_reader.serial.Serial",
        side_effect=serial.SerialException("Port not found"),
    )

    with pytest.raises(serial.SerialException):
        read_frame("/dev/ttyUSB0")


# ── recorded frame round-trip ──────────────────────────────────────────────


RECORDED_FRAME = (
    b"\x02\nADCO 021861348497 L\r\nOPTARIF BBR( S\r\nISOUSC 30 9\r"
    b"\nBBRHCJB 018328702 <\r\nBBRHPJB 023739545 P\r\nBBRHCJW 001466099 U\r"
    b"\nBBRHPJW 002132883 Z\r\nBBRHCJR 000860118 E\r\nBBRHPJR 000844115 Q\r"
    b"\nPTEC HCJB C\r\nDEMAIN ROUG +\r\nIINST 012 Z\r\nIMAX 090 H\r"
    b"\nPAPP 02830 .\r\nHHPHC A ,\r\nMOTDETAT 000000 B\r\x03"
)


def test_read_frame_with_recorded_frame(mock_serial):
    _, mock_ser = mock_serial
    mock_ser.read.side_effect = _bytes_to_reads(RECORDED_FRAME)

    result = read_frame("/dev/ttyUSB0")

    assert_that(result, equal_to(RECORDED_FRAME))
