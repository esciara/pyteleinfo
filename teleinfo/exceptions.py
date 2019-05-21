class TeleinfoError(Exception):
    """Basic exception for errors raised by teleinfo"""


class BaseFormatError(TeleinfoError):
    """The format of a frame is invalid"""

    def __init__(self, string_verified, object_type_verified: str,
                 errors: str = None):
        if isinstance(string_verified, str):
            string_verified = string_verified.encode()
        msg = "{} format verified: '{}'".format(object_type_verified,
                                                string_verified)
        if errors is not None:
            msg = ' | '.join([msg, errors])
        super().__init__(msg)


class FrameFormatError(BaseFormatError):
    """The format of a frame is invalid"""

    def __init__(self, frame, errors: str = None):
        super().__init__(string_verified=frame, object_type_verified="Frame",
                         errors=errors)


class InfoGroupFormatError(BaseFormatError):
    """The format of a group of information within a frame is invalid"""

    def __init__(self, info_group: str, errors: str = None):
        super().__init__(string_verified=info_group,
                         object_type_verified="Info group", errors=errors)


class ChecksumError(TeleinfoError):
    """The checksum of a group of information within a frame is invalid"""

    def __init__(self, label_data_and_separators, checksum, checksum_1, checksum_2,
                 msg=None):
        if msg is None:
            msg = 'Needed checksum \'{}\' to validate the info group \'{}\', ' \
                  'but was neither matched by neither method 1 checksum (= \'{}\'), ' \
                  'nor by method 2 checksum (= \'{}\')'.format(checksum,
                                                               label_data_and_separators,
                                                               checksum_1,
                                                               checksum_2)
        super().__init__(msg)
