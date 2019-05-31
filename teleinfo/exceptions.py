"""
All package specific exceptions
"""


class TeleinfoError(Exception):
    """Base exception for errors raised by teleinfo"""


class TeleinfoDecodingError(TeleinfoError):
    """Base exception for errors raised by teleinfo during decoding of a frame"""


class BaseFormatError(TeleinfoDecodingError):
    """The format of a frame is invalid"""

    def __init__(self, string_verified, object_type_verified: str, errors: str = None):
        if isinstance(string_verified, str):
            string_verified = string_verified.encode()
        msg = "{} format verified: '{}'".format(object_type_verified, string_verified)
        if errors is not None:
            msg = " | ".join([msg, errors])
        super().__init__(msg)


class FrameFormatError(BaseFormatError):
    """The format of a frame is invalid"""

    def __init__(self, frame, errors: str = None):
        super().__init__(
            string_verified=frame, object_type_verified="Frame", errors=errors
        )


class InfoGroupFormatError(BaseFormatError):
    """The format of a group of information within a frame is invalid"""

    def __init__(self, info_group: str, errors: str = None):
        super().__init__(
            string_verified=info_group, object_type_verified="Info group", errors=errors
        )


class ChecksumError(TeleinfoDecodingError):
    """The checksum of a group of information within a frame is invalid"""

    def __init__(self, label_data_and_separators, checksums, msg=None):
        if msg is None:
            msg = (
                "Needed checksum '{}' to validate the info group '{}', "
                "but was neither matched by method 1 checksum (= '{}'), "
                "nor by method 2 checksum (= '{}')".format(
                    checksums[0], label_data_and_separators, checksums[1], checksums[2]
                )
            )
        super().__init__(msg)
