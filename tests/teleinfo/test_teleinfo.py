# pylint: disable=missing-docstring

from hamcrest import assert_that, equal_to

from teleinfo import decode


def test_decode_recorded_frame_returns_expected_dict(recorded_frame_1, recorded_frame_1_expected):
    result = decode(recorded_frame_1)

    assert_that(result, equal_to(recorded_frame_1_expected))
