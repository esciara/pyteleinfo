# pylint: disable=missing-docstring

import pytest
from hamcrest import assert_that, calling, equal_to, not_, raises

from teleinfo.codec import (
    _extract_info_groups,
    _extract_info_groups_positions,
    _extract_label_and_data,
    _verify_checksum,
    _verify_frame_list_well_formed,
    _verify_frame_well_formed,
    _verify_info_group_well_formed,
    decode,
    decode_from_list,
    decode_info_group,
    encode,
    encode_info_group,
)
from teleinfo.const import (
    CR_TOKEN,
    DATA_KEY,
    ETX_TOKEN,
    HT_TOKEN,
    LABEL_KEY,
    LF_TOKEN,
    SP_TOKEN,
    STX_TOKEN,
)
from teleinfo.exceptions import (
    BaseFormatError,
    ChecksumError,
    FrameFormatError,
    InfoGroupFormatError,
)


LABEL_DATA_SEP_TEMPLATE = "{label}{SEP}{data}{SEP}"

INFO_GROUP_TEMPLATE = "{LF}" + LABEL_DATA_SEP_TEMPLATE + "{checksum}{CR}"


def test_encode_whole_frame():
    # Given the following frame data
    frame_data = [
        {LABEL_KEY: "ADCO", DATA_KEY: "524563565245"},
        {LABEL_KEY: "OPTARIF", DATA_KEY: "HC.."},
    ]

    # When I encode the frame data
    result = encode(frame_data)

    # Then I should obtain the following encoding
    expected = "".join(
        [
            "{}".format(STX_TOKEN),
            encode_info_group(frame_data[0][LABEL_KEY], frame_data[0][DATA_KEY]),
            encode_info_group(frame_data[1][LABEL_KEY], frame_data[1][DATA_KEY]),
            "{}".format(ETX_TOKEN),
        ]
    )

    assert_that(result, equal_to(expected), "Frame not encoded as expected")


def test_encode_info_group_passes():
    # Given the following 'group of information'
    label = "ADCO"
    data = "050022120078"

    # When I encode this group
    result = encode_info_group(label, data)

    # Then I should obtain the following encoding
    expected = INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum="2", CR=CR_TOKEN)
    assert_that(result, equal_to(expected), "Info Group not encoded as expected")


def test_decode_frame_passes(valid_frame, valid_frame_json):
    # Given the following frame
    frame = valid_frame

    # When I encode the frame data
    try:
        result = decode(frame)
    except BaseFormatError as e:
        pytest.fail("Decoding failed {}".format(e))

    # Then I should obtain the following encoding
    expected = valid_frame_json

    assert_that(result, equal_to(expected), "Frame not decoded as expected")


def test_decode_frame_as_list_passes():
    # Given the following frame
    frame = [
        STX_TOKEN,
        INFO_GROUP_TEMPLATE.format(
            LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
        ),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
        ETX_TOKEN,
    ]

    # When I encode the frame data
    try:
        result = decode_from_list(frame)
    except BaseFormatError as e:
        pytest.fail("Decoding failed {}".format(e))

    # Then I should obtain the following encoding
    expected = {"ADCO": "050022120078", "OPTARIF": "HC..", "ISOUSC": "45"}

    assert_that(result, equal_to(expected), "Frame not decoded as expected")


def test_decode_info_group_passes():
    # Given the following encoded 'group of information'
    label = "ADCO"
    data = "524563565245"
    checksum = " "
    encoded_info_group = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum=checksum, CR=CR_TOKEN
    )

    # When I decode this group
    result = decode_info_group(encoded_info_group, verify_well_formed=False, verify_checksum=False)

    # Then I should obtain the following decoded label and data
    expected = (label, data)
    assert_that(result, equal_to(expected), "Info Group not decoded as expected")


def test_extract_label_and_data_where_data_without_separator_chars():
    # Given the following encoded label, data and separators core
    label = "ADCO"
    data = "524563565245"
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP_TOKEN, data=data)

    # When I extract the label and data
    result = _extract_label_and_data(label_data_and_separators)

    # Then I should obtain the following decoded label and data
    expected = (label, data)
    assert_that(result, equal_to(expected), "Extracted label and data not as expected")


def test_extract_label_and_data_where_data_contains_separator_chars():
    # Given the following encoded label, data and separators core
    label = "ADCO"
    data_left = "524563"
    data_right = "565245"
    data = "{data_left}{SEP}{data_right}".format(data_left=data_left, SEP=SP_TOKEN, data_right=data_right)
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP_TOKEN, data=data)

    # When I extract the label and data
    result = _extract_label_and_data(label_data_and_separators)

    # Then I should obtain the following decoded label and data
    expected = (label, data)
    assert_that(result, equal_to(expected), "Extracted label and data not as expected")


def test_verify_checksum_method_1():
    # Given the following encoded label, data and separators core
    label = "ADCO"
    data = "050022120078"
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP_TOKEN, data=data)

    # And the following checksum
    checksum = "2"

    # When I verify the checksum calculated
    # Then it should be calculated correctly
    assert_that(
        calling(_verify_checksum).with_args(label_data_and_separators, checksum),
        not_(raises(ChecksumError)),
        "Checksum calculated with method 1 expected to match but did not",
    )


def test_verify_checksum_method_2():
    # Given the following encoded label, data and separators core
    label = "ADCO"
    data = "050022120078"
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP_TOKEN, data=data)

    # And the following checksum
    checksum = "R"

    # When I verify the checksum calculated
    # Then it should be calculated correctly
    assert_that(
        calling(_verify_checksum).with_args(label_data_and_separators, checksum),
        not_(raises(ChecksumError)),
        "Checksum calculated with method 2 expected to match but did not",
    )


def test_verify_checksum_raises_exception_on_incorrect_checksum():
    # Given the following encoded label, data and separators core
    label = "ADCO"
    data = "050022120078"
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP_TOKEN, data=data)

    # And the following checksum
    checksum = "x"

    # When I verify the checksum calculations for both method 1 and 2
    # Then they should be calculated correctly
    assert_that(
        calling(_verify_checksum).with_args(label_data_and_separators, checksum),
        raises(ChecksumError, r"\bNeeded checksum 'x' to validate the info group\b"),
        "Checksum verification should have failed but passes",
    )


def test_verify_frame_well_formed():
    # Given the following frame
    frame = "".join(
        [
            STX_TOKEN,
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
            ETX_TOKEN,
        ]
    )

    # When I verify the frame is well formed
    # Then it should be validated as correct
    assert_that(
        calling(_verify_frame_well_formed).with_args(frame),
        not_(raises(FrameFormatError)),
        "Frame format should have been verified as correct",
    )


def test_verify_frame_well_formed_raises_exception_on_incorrect_first_char():
    # Given the following frame with CR as first character
    frame = "".join(
        [
            CR_TOKEN,
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
            ETX_TOKEN,
        ]
    )

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_frame_well_formed).with_args(frame),
        raises(FrameFormatError, r"\bFirst char should be STX but is\b"),
        "Frame format should have been verified as correct",
    )


def test_verify_frame_well_formed_raises_exception_on_incorrect_last_char():
    # Given the following frame with LF as last character
    frame = "".join(
        [
            STX_TOKEN,
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
            LF_TOKEN,
        ]
    )

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_frame_well_formed).with_args(frame),
        raises(FrameFormatError, r"\bLast char should be ETX but is\b"),
        "Frame format should have been verified as correct",
    )


def test_verify_frame_well_formed_raises_exception_on_missing_cr_or_lf():
    # Given the following frames, one with CR missing and one with LF missing
    frame = "".join(
        [
            STX_TOKEN,
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
            ETX_TOKEN,
        ]
    )
    frame_cr_missing = frame.replace(CR_TOKEN, "", 1)
    frame_lf_missing = frame.replace(LF_TOKEN, "", 1)

    # When I verify each frame is well formed
    # Then it should raise an exception
    assert_that(
        calling(_verify_frame_well_formed).with_args(frame_cr_missing),
        raises(FrameFormatError, r"\bShould have as many beginnings\b"),
        "Frame format should have been verified as correct",
    )
    assert_that(
        calling(_verify_frame_well_formed).with_args(frame_lf_missing),
        raises(FrameFormatError, r"\bShould have as many beginnings\b"),
        "Frame format should have been verified as correct",
    )


def test_verify_frame_well_formed_raises_exception_on_cr_before_lf():
    # Given the following frame with one CR and one LF inverted
    frame = "".join(
        [
            STX_TOKEN,
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
            ETX_TOKEN,
        ]
    )
    frame = frame.replace(CR_TOKEN, LF_TOKEN, 1)
    frame = frame.replace(LF_TOKEN, CR_TOKEN, 1)

    # When I verify each frame is well formed
    # Then it should raise an exception
    assert_that(
        calling(_verify_frame_well_formed).with_args(frame),
        raises(
            FrameFormatError,
            r"\bShould always have a LF followed by a CR to delimit info groups, " r"but some where inverted\b",
        ),
        "Frame format should have been verified as correct",
    )


def test_extract_info_groups():
    # Given the following frame
    group1 = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
    )
    group2 = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
    )
    group3 = INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN)
    frame = "".join([STX_TOKEN, group1, group2, group3, ETX_TOKEN])

    # When I extract the info groups
    info_groups = _extract_info_groups(frame)

    # Then I should obtain the following list of info groups
    expected = [group1, group2, group3]
    assert_that(info_groups, equal_to(expected))


def test_extract_info_groups_positions():
    # Given the following frame
    frame = "".join(
        [
            STX_TOKEN,
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(
                LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN
            ),
            INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
            ETX_TOKEN,
        ]
    )

    # When I extract the info groups positions
    beginnings, ends = _extract_info_groups_positions(frame)

    # Then I should obtain the following beginnings and ends
    expected = ([1, 22, 38], [21, 37, 50])
    assert_that((beginnings, ends), equal_to(expected))


def test_verify_frame_list_well_formed():
    # Given the following frame
    frame_list = [
        STX_TOKEN,
        INFO_GROUP_TEMPLATE.format(
            LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
        ),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
        ETX_TOKEN,
    ]

    # When I verify the frame is well formed
    # Then it should be validated as correct
    assert_that(
        calling(_verify_frame_list_well_formed).with_args(frame_list),
        not_(raises(FrameFormatError)),
        "Frame format should have been verified as correct",
    )


def test_verify_frame_list_well_formed_raises_exception_on_incorrect_first_char():
    # Given the following frame with CR as first character
    frame_list = [
        CR_TOKEN,
        INFO_GROUP_TEMPLATE.format(
            LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
        ),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
        ETX_TOKEN,
    ]

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_frame_list_well_formed).with_args(frame_list),
        raises(FrameFormatError, r"\bFirst char should be STX but is\b"),
        "Frame format should have been verified as correct",
    )


def test_verify_frame_list_well_formed_raises_exception_on_incorrect_last_char():
    # Given the following frame with LF as last character
    frame_list = [
        STX_TOKEN,
        INFO_GROUP_TEMPLATE.format(
            LF=LF_TOKEN, label="ADCO", SEP=SP_TOKEN, data="050022120078", checksum="2", CR=CR_TOKEN
        ),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="OPTARIF", SEP=SP_TOKEN, data="HC..", checksum="<", CR=CR_TOKEN),
        INFO_GROUP_TEMPLATE.format(LF=LF_TOKEN, label="ISOUSC", SEP=SP_TOKEN, data="45", checksum="?", CR=CR_TOKEN),
        LF_TOKEN,
    ]

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_frame_list_well_formed).with_args(frame_list),
        raises(FrameFormatError, r"\bLast char should be ETX but is\b"),
        "Frame format should have been verified as correct",
    )


def test_verify_info_group_well_formed():
    # Given the following encoded 'group of information'
    label = "ADCO"
    data = "050022120078"
    checksum = "x"
    encoded_info_group = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum=checksum, CR=CR_TOKEN
    )

    # When I verify the info group is well formed
    # Then it should be validated as correct
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        not_(raises(InfoGroupFormatError)),
        "Info group format should have been verified as correct",
    )


def test_verify_info_group_well_formed_raises_exception_on_incorrect_first_char():
    # Given the following encoded 'group of information' with CR as first character
    label = "ADCO"
    data = "050022120078"
    checksum = "x"
    encoded_info_group = INFO_GROUP_TEMPLATE.format(
        LF=CR_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum=checksum, CR=CR_TOKEN
    )

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError, r"\bFirst char should be LF but is\b"),
        "Info group format should have been verified as correct",
    )


def test_verify_info_group_well_formed_raises_exception_on_incorrect_last_char():
    # Given the following encoded 'group of information' with LF as last character
    label = "ADCO"
    data = "050022120078"
    checksum = "x"
    encoded_info_group = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum=checksum, CR=LF_TOKEN
    )

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError, r"\bLast char should be CR but is\b"),
        "Info group format should have been verified as correct",
    )


def test_verify_info_group_well_formed_raises_exception_on_separator_mix():
    # Given the following encoded 'group of information' with one missing separator
    label = "ADCO"
    data = "050022120078"
    checksum = "x"
    encoded_info_group = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum=checksum, CR=CR_TOKEN
    )
    encoded_info_group = encoded_info_group.replace(SP_TOKEN, HT_TOKEN, 1)

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError, r"\bShould not contain both CR and HT separators\b"),
        "Info Group Format should have been verified as correct",
    )


def test_verify_info_group_well_formed_raises_exception_on_too_few_separators():
    # Given the following encoded 'group of information' with one missing separator
    label = "ADCO"
    data = "050022120078"
    checksum = "x"
    encoded_info_group = INFO_GROUP_TEMPLATE.format(
        LF=LF_TOKEN, label=label, SEP=SP_TOKEN, data=data, checksum=checksum, CR=CR_TOKEN
    )
    encoded_info_group = encoded_info_group.replace(SP_TOKEN, "", 1)

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(
            InfoGroupFormatError,
            r"\bShould contain at least 2 separators but has only\b",
        ),
        "Info Group Format should have been verified as correct",
    )
