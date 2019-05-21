import pytest
from hamcrest import *
from teleinfo.codec import *
from teleinfo.codec import (_extract_label_and_data,
                            _extract_info_groups_positions,
                            _extract_info_groups,
                            _verify_frame_well_formed,
                            _verify_frame_list_well_formed,
                            _verify_info_group_well_formed,
                            _verify_checksum)
from teleinfo.const import *

LABEL_DATA_SEP_TEMPLATE = "{label}{SEP}{data}{SEP}"

INFO_GROUP_TEMPLATE = "{LF}" + LABEL_DATA_SEP_TEMPLATE + "{checksum}{CR}"


def test_encode_frame():
    # Given the following frame data
    frame_data = [{LABEL: 'ADCO', DATA: '524563565245'},
                  {LABEL: 'OPTARIF', DATA: 'HC..'}]

    # When I encode the frame data
    result = encode(frame_data)

    # Then I should obtain the following encoding
    expected = ''.join(['{}'.format(STX),
                        encode_info_group(frame_data[0][LABEL], frame_data[0][DATA]),
                        encode_info_group(frame_data[1][LABEL], frame_data[1][DATA]),
                        '{}'.format(ETX)])

    assert_that(result, equal_to(expected), 'Frame not encoded as expected')


def test_encode_info_group():
    # Given the following 'group of information'
    label = 'ADCO'
    data = '050022120078'

    # When I encode this group
    result = encode_info_group(label, data)

    # Then I should obtain the following encoding
    expected = INFO_GROUP_TEMPLATE.format(LF=LF, label=label, SEP=SP, data=data,
                                          checksum='2', CR=CR)
    assert_that(result, equal_to(expected), 'Info Group not encoded as expected')


def test_decode_frame(valid_frame, valid_frame_json):
    # Given the following frame
    frame = valid_frame

    # When I encode the frame data
    try:
        result = decode(frame)
    except BaseFormatError as e:
        pytest.fail('Decoding failed {}'.format(e))

    # Then I should obtain the following encoding
    expected = valid_frame_json

    assert_that(result, equal_to(expected), 'Frame not decoded as expected')


def test_decode_frame_as_list():
    # Given the following frame
    frame = [STX,
             INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                        data='050022120078', checksum='2', CR=CR),
             INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP, data='HC..',
                                        checksum='<', CR=CR),
             INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP, data='45',
                                        checksum='?', CR=CR),
             ETX]

    # When I encode the frame data
    try:
        result = decode_from_list(frame)
    except BaseFormatError as e:
        pytest.fail('Decoding failed {}'.format(e))

    # Then I should obtain the following encoding
    expected = {'ADCO': '050022120078', 'OPTARIF': 'HC..', 'ISOUSC': '45'}

    assert_that(result, equal_to(expected), 'Frame not decoded as expected')


def test_decode_info_group():
    # Given the following encoded 'group of information'
    label = 'ADCO'
    data = '524563565245'
    checksum = ' '
    encoded_info_group = INFO_GROUP_TEMPLATE.format(LF=LF, label=label, SEP=SP,
                                                    data=data, checksum=checksum,
                                                    CR=CR)

    # When I decode this group
    result = decode_info_group(encoded_info_group, verify_well_formed=False,
                               verify_checksum=False)

    # Then I should obtain the following decoded label and data
    expected = (label, data)
    assert_that(result, equal_to(expected), 'Info Group not decoded as expected')


def test_extract_label_and_data_where_data_without_separator_chars():
    # Given the following encoded label, data and separators core
    label = 'ADCO'
    data = '524563565245'
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP,
                                                               data=data)

    # When I extract the label and data
    result = _extract_label_and_data(label_data_and_separators)

    # Then I should obtain the following decoded label and data
    expected = (label, data)
    assert_that(result, equal_to(expected),
                'Extracted label and data not as expected')


def test_extract_label_and_data_where_data_contains_separator_chars():
    # Given the following encoded label, data and separators core
    label = 'ADCO'
    data_left = '524563'
    data_right = '565245'
    data = "{data_left}{SEP}{data_right}".format(data_left=data_left, SEP=SP,
                                                 data_right=data_right)
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP,
                                                               data=data)

    # When I extract the label and data
    result = _extract_label_and_data(label_data_and_separators)

    # Then I should obtain the following decoded label and data
    expected = (label, data)
    assert_that(result, equal_to(expected),
                'Extracted label and data not as expected')


def test_verify_checksum_method_1():
    # Given the following encoded label, data and separators core
    label = 'ADCO'
    data = '050022120078'
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP,
                                                               data=data)

    # And the following checksum
    checksum = '2'

    # When I verify the checksum calculated
    # Then it should be calculated correctly
    assert_that(
        calling(_verify_checksum).with_args(label_data_and_separators, checksum),
        not_(raises(ChecksumError)),
        'Checksum calculated with method 1 expected to match but did not')


def test_verify_checksum_method_2():
    # Given the following encoded label, data and separators core
    label = 'ADCO'
    data = '050022120078'
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP,
                                                               data=data)

    # And the following checksum
    checksum = 'R'

    # When I verify the checksum calculated
    # Then it should be calculated correctly
    assert_that(
        calling(_verify_checksum).with_args(label_data_and_separators, checksum),
        not_(raises(ChecksumError)),
        'Checksum calculated with method 2 expected to match but did not')


def test_verify_checksum_raises_exception_on_incorrect_checksum():
    # Given the following encoded label, data and separators core
    label = 'ADCO'
    data = '050022120078'
    label_data_and_separators = LABEL_DATA_SEP_TEMPLATE.format(label=label, SEP=SP,
                                                               data=data)

    # And the following checksum
    checksum = 'x'

    # When I verify the checksum calculations for both method 1 and 2
    # Then they should be calculated correctly
    assert_that(
        calling(_verify_checksum).with_args(label_data_and_separators, checksum),
        raises(ChecksumError),
        'Checksum verification should have failed but passes')


def test_verify_frame_well_formed():
    # Given the following frame
    frame = ''.join([STX,
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                                data='050022120078', checksum='2',
                                                CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                                data='HC..', checksum='<', CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                                data='45', checksum='?', CR=CR),
                     ETX])

    # When I verify the frame is well formed
    # Then it should be validated as correct
    assert_that(calling(_verify_frame_well_formed).with_args(frame),
                not_(raises(FrameFormatError)),
                'Frame format should have been verified as correct')


def test_verify_frame_well_formed_raises_exception_on_incorrect_first_char():
    # Given the following frame with CR as first character
    frame = ''.join([CR,
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                                data='050022120078', checksum='2',
                                                CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                                data='HC..', checksum='<', CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                                data='45', checksum='?', CR=CR),
                     ETX])

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(calling(_verify_frame_well_formed).with_args(frame),
                raises(FrameFormatError,
                       r'\bFirst char should be STX but is\b'),
                'Frame format should have been verified as correct')


def test_verify_frame_well_formed_raises_exception_on_incorrect_last_char():
    # Given the following frame with LF as last character
    frame = ''.join([STX,
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                                data='050022120078', checksum='2',
                                                CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                                data='HC..', checksum='<', CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                                data='45', checksum='?', CR=CR),
                     LF])

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(calling(_verify_frame_well_formed).with_args(frame),
                raises(FrameFormatError,
                       r'\bLast char should be ETX but is\b'),
                'Frame format should have been verified as correct')


def test_verify_frame_well_formed_raises_exception_on_missing_cr_or_lf():
    # Given the following frames, one with CR missing and one with LF missing
    frame = ''.join([STX,
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                                data='050022120078', checksum='2',
                                                CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                                data='HC..', checksum='<', CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                                data='45', checksum='?', CR=CR),
                     ETX])
    frame_cr_missing = frame.replace(CR, '', 1)
    frame_lf_missing = frame.replace(LF, '', 1)

    # When I verify each frame is well formed
    # Then it should raise an exception
    assert_that(calling(_verify_frame_well_formed).with_args(frame_cr_missing),
                raises(FrameFormatError,
                       r'\bShould have as many beginnings\b'),
                'Frame format should have been verified as correct')
    assert_that(calling(_verify_frame_well_formed).with_args(frame_lf_missing),
                raises(FrameFormatError,
                       r'\bShould have as many beginnings\b'),
                'Frame format should have been verified as correct')


def test_verify_frame_well_formed_raises_exception_on_cr_before_lf():
    # Given the following frame with one CR and one LF inverted
    frame = ''.join([STX,
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                                data='050022120078', checksum='2',
                                                CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                                data='HC..', checksum='<', CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                                data='45', checksum='?', CR=CR),
                     ETX])
    frame = frame.replace(CR, LF, 1)
    frame = frame.replace(LF, CR, 1)

    # When I verify each frame is well formed
    # Then it should raise an exception
    assert_that(calling(_verify_frame_well_formed).with_args(frame),
                raises(FrameFormatError,
                       r'\bShould always have a LF followed by a CR to delimit info groups, but some where inverted\b'),
                'Frame format should have been verified as correct')


def test_extract_info_groups():
    # Given the following frame
    group1 = INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                        data='050022120078', checksum='2', CR=CR)
    group2 = INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP, data='HC..',
                                        checksum='<', CR=CR)
    group3 = INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP, data='45',
                                        checksum='?', CR=CR)
    frame = ''.join([STX,
                     group1,
                     group2,
                     group3,
                     ETX])

    # When I extract the info groups
    info_groups = _extract_info_groups(frame)

    # Then I should obtain the following list of info groups
    expected = [group1, group2, group3]
    assert_that(info_groups, equal_to(expected))


def test_extract_info_groups_positions():
    # Given the following frame
    frame = ''.join([STX,
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                                data='050022120078', checksum='2',
                                                CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                                data='HC..', checksum='<', CR=CR),
                     INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                                data='45', checksum='?', CR=CR),
                     ETX])

    # When I extract the info groups positions
    beginnings, ends = _extract_info_groups_positions(frame)

    # Then I should obtain the following beginnings and ends
    expected = ([1, 22, 38], [21, 37, 50])
    assert_that((beginnings, ends), equal_to(expected))


def test_verify_frame_list_well_formed():
    # Given the following frame
    frame_list = [STX,
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                             data='050022120078', checksum='2',
                                             CR=CR),
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                             data='HC..', checksum='<', CR=CR),
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                             data='45', checksum='?', CR=CR),
                  ETX]

    # When I verify the frame is well formed
    # Then it should be validated as correct
    assert_that(calling(_verify_frame_list_well_formed).with_args(frame_list),
                not_(raises(FrameFormatError)),
                'Frame format should have been verified as correct')


def test_verify_frame_list_well_formed_raises_exception_on_incorrect_first_char():
    # Given the following frame with CR as first character
    frame_list = [CR,
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                             data='050022120078', checksum='2',
                                             CR=CR),
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                             data='HC..', checksum='<', CR=CR),
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                             data='45', checksum='?', CR=CR),
                  ETX]

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(calling(_verify_frame_list_well_formed).with_args(frame_list),
                raises(FrameFormatError,
                       r'\bFirst char should be STX but is\b'),
                'Frame format should have been verified as correct')


def test_verify_frame_list_well_formed_raises_exception_on_incorrect_last_char():
    # Given the following frame with LF as last character
    frame_list = [STX,
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='ADCO', SEP=SP,
                                             data='050022120078', checksum='2',
                                             CR=CR),
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='OPTARIF', SEP=SP,
                                             data='HC..', checksum='<', CR=CR),
                  INFO_GROUP_TEMPLATE.format(LF=LF, label='ISOUSC', SEP=SP,
                                             data='45', checksum='?', CR=CR),
                  LF]

    # When I verify the frame is well formed
    # Then it raise an exception
    assert_that(calling(_verify_frame_list_well_formed).with_args(frame_list),
                raises(FrameFormatError,
                       r'\bLast char should be ETX but is\b'),
                'Frame format should have been verified as correct')


def test_verify_info_group_well_formed():
    # Given the following encoded 'group of information'
    label = 'ADCO'
    data = '050022120078'
    checksum = 'x'
    encoded_info_group = INFO_GROUP_TEMPLATE.format(LF=LF, label=label, SEP=SP,
                                                    data=data, checksum=checksum,
                                                    CR=CR)

    # When I verify the info group is well formed
    # Then it should be validated as correct
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        not_(raises(InfoGroupFormatError)),
        'Info group format should have been verified as correct')


def test_verify_info_group_well_formed_raises_exception_on_incorrect_first_char():
    # Given the following encoded 'group of information' with CR as first character
    label = 'ADCO'
    data = '050022120078'
    checksum = 'x'
    encoded_info_group = INFO_GROUP_TEMPLATE.format(LF=CR, label=label, SEP=SP,
                                                    data=data, checksum=checksum,
                                                    CR=CR)

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError,
               r'\bFirst char should be LF but is\b'),
        'Info group format should have been verified as correct')


def test_verify_info_group_well_formed_raises_exception_on_incorrect_last_char():
    # Given the following encoded 'group of information' with LF as last character
    label = 'ADCO'
    data = '050022120078'
    checksum = 'x'
    encoded_info_group = INFO_GROUP_TEMPLATE.format(LF=LF, label=label, SEP=SP,
                                                    data=data, checksum=checksum,
                                                    CR=LF)

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError,
               r'\bLast char should be CR but is\b'),
        'Info group format should have been verified as correct')


def test_verify_info_group_well_formed_raises_exception_on_separator_mix():
    # Given the following encoded 'group of information' with one missing separator
    label = 'ADCO'
    data = '050022120078'
    checksum = 'x'
    encoded_info_group = INFO_GROUP_TEMPLATE.format(LF=LF, label=label, SEP=SP,
                                                    data=data, checksum=checksum,
                                                    CR=CR)
    encoded_info_group = encoded_info_group.replace(SP, HT, 1)

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError,
               r'\bShould not contain both CR and HT separators\b'),
        'Info Group Format should have been verified as correct')


def test_verify_info_group_well_formed_raises_exception_on_too_few_separators():
    # Given the following encoded 'group of information' with one missing separator
    label = 'ADCO'
    data = '050022120078'
    checksum = 'x'
    encoded_info_group = INFO_GROUP_TEMPLATE.format(LF=LF, label=label, SEP=SP,
                                                    data=data, checksum=checksum,
                                                    CR=CR)
    encoded_info_group = encoded_info_group.replace(SP, '', 1)

    # When I verify the info group is well formed
    # Then it raise an exception
    assert_that(
        calling(_verify_info_group_well_formed).with_args(encoded_info_group),
        raises(InfoGroupFormatError,
               r'\bShould contain at least 2 separators but has only\b'),
        'Info Group Format should have been verified as correct')
