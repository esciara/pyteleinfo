"""Top-level module for pyteleinfo.

This module import the version of the package

"""

from .__version__ import __version__  # noqa
from .codec import decode  # noqa
from .exceptions import (  # noqa
    BaseFormatError,
    ChecksumError,
    FrameFormatError,
    InfoGroupFormatError,
    TeleinfoDecodingError,
    TeleinfoError,
)
from .serial_reader import read_frame  # noqa
