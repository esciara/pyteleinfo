"""
This module includes functions to decode/encode teleinfo data strings in/from json.
It also can accept bytes for decoding:

.. code-block:: python

    json_frame = {
        "ADCO": "050022120078",
        "OPTARIF": "HC..",
    #   ...
        }

    #     <=>

    string_frame = (
        "\\x02"
        "\\nADCO 050022120078 2\\r"
        "\\nOPTARIF HC.. <\\r"
    #   ...
    )

This is an implementation of the
`tele-information communication frames specifications for french electronic electricity
meters <https://www.enedis.fr/sites/default/files/Enedis-NOI-CPT_02E.pdf>`_,
and that is  (not tested on Linky, but probably should work).

Definitions:

* *tele-information (teleinfo) frame*: a complete set of information transmited by the
  electronic electricity meter at instant t.
* *Information group (info group)*: tuple of (label, data, checksum) in string format
  - or (label, data) in json format - representing one information transmitted
  through the frame.
"""

import re

from teleinfo.const import CR, DATA, ENCODING, ETX, HT, LABEL, LF, SP, STX
from teleinfo.exceptions import ChecksumError, FrameFormatError, InfoGroupFormatError


def encode(info_groups: dict) -> str:
    """
    Encodes a teleinfo frame in json format to string format.

    :param info_groups: teleinfo data json
    :return: teleinfo data string
    """
    encoded_info_groups = "".join(
        [
            encode_info_group(info_group[LABEL], info_group[DATA])
            for info_group in info_groups
        ]
    )
    return "".join(["{}".format(STX), encoded_info_groups, "{}".format(ETX)])


def decode(frame, verify_well_formed: bool = True) -> dict:
    """
    Decodes a teleinfo frame from string or bytes format to json format.

    :param frame: str or bytes, teleinfo frame in string or bytes format
    :param verify_well_formed: if True, verifies that the frame is well formed
    :return: a json dict of (label, data) key/value pair extracted from the frame
    """
    # TODO: check that there is not EOT character in the frame. If there is, handle it
    # Encode frame in ENCODING (normally ascii) if frame is still in bytes
    if isinstance(frame, bytes):
        frame = frame.decode(ENCODING)

    if verify_well_formed:
        _verify_frame_well_formed(frame)
    extracted_info_groups = _extract_info_groups(frame)
    decoded_frame = {}
    for info_group in extracted_info_groups:
        label, data = decode_info_group(info_group)
        decoded_frame[label] = data
    return decoded_frame


def decode_from_list(frame_list: list, verify_well_formed: bool = True) -> dict:
    """
    Same as decode, but receives a list as parameter. (probably should be deprecated)

    :param frame: teleinfo frame in list format
    :param verify_well_formed: if True, verifies that the frame is well formed
    :return: a json dict of (label, data) key/value pair extracted from the frame
    """
    if verify_well_formed:
        _verify_frame_list_well_formed(frame_list)
    decoded_frame = {}
    # Remove first item (STX) and last item (ETX)
    frame_list_trimmed = frame_list[1:-1]
    for info_group in frame_list_trimmed:
        label, data = decode_info_group(info_group)
        decoded_frame[label] = data
    return decoded_frame


def encode_info_group(label: str, data: str, sep: str = SP) -> str:
    """
    Encodes data of an info group into string format

    :param label: info group label
    :param data: info group data
    :param sep: separator that will be used (normally SP but could be HT)
    :return: info group in string format
    """
    encoded_info_group = "{label}{SEP}{data}{SEP}".format(
        label=label, SEP=sep, data=data
    )
    checksum = _checksum_method_1(encoded_info_group)
    return "{LF}{encoded_info_group}{checksum}{CR}".format(
        LF=LF, encoded_info_group=encoded_info_group, checksum=checksum, CR=CR
    )


def decode_info_group(
    encoded_info_group: str,
    verify_well_formed: bool = True,
    verify_checksum: bool = True,
) -> (str, str):
    """
    Decodes info group from string format to extract label and data.

    :param encoded_info_group: info group from the frame, in string format
    :param verify_well_formed: if True, verifies that the info group is well formed
    :param verify_checksum: if True, verifies info group's checksum
    :return: (label, data) extracted from the info group
    """
    if verify_well_formed:
        _verify_info_group_well_formed(encoded_info_group)
    # Remove first char (LF) and last char (CR)
    encoded_info_group_trimmed = encoded_info_group[1:-1]
    # Extracting checksum
    label_data_and_separators, checksum = (
        encoded_info_group_trimmed[:-1],
        encoded_info_group_trimmed[-1:],
    )
    if verify_checksum:
        _verify_checksum(label_data_and_separators, checksum)
    label, data = _extract_label_and_data(label_data_and_separators)
    return label, data


def _append_error(errors, error):
    errors = " | ".join([errors, error]) if errors is not None else error
    return errors


def _verify_frame_well_formed(frame: str):
    """
    Etape B : effectuer le stockage de la totalité de la trame avec vérification
    de sa conformité protocolaire (caractère ASCII « STX » – présence d’un corps
    d’au moins un groupe – caractère ASCII « ETX » (ou caractère ASCII « EOT »
    en cas d'interruption).

    :param frame: str
    :return: None
    :raises: FrameFormatError
    """
    errors = None
    first_char, last_char = frame[:1], frame[-1:]
    beginnings, ends = _extract_info_groups_positions(frame)

    if first_char != STX:
        error = "First char should be STX but is '{}'".format(first_char.encode())
        errors = _append_error(errors, error)
    if last_char != ETX:
        error = "Last char should be ETX but is '{}'".format(last_char.encode())
        errors = _append_error(errors, error)
    if len(beginnings) != len(ends):
        error = (
            "Should have as many beginnings (LF) as ends (CR) to delimit info "
            "groups, but had ({}, {})".format(len(beginnings), len(ends))
        )
        errors = _append_error(errors, error)
    else:
        results = [i > j for (i, j) in zip(beginnings, ends)]
        if any(results):
            indices = [i for i, x in enumerate(results) if x is True]
            faulty_pairs = [(beginnings[i], ends[i]) for i in indices]
            error = (
                "Should always have a LF followed by a CR to delimit "
                "info groups, but some where inverted "
                "(pairs of LF/CR indices: {})".format(faulty_pairs)
            )
            errors = _append_error(errors, error)
    if errors is not None:
        raise FrameFormatError(frame, errors)


def _extract_info_groups_positions(frame: str) -> (dict, dict):
    info_groups_beginnings = [m.start() for m in re.finditer(LF, frame)]
    info_groups_ends = [m.start() for m in re.finditer(CR, frame)]
    return info_groups_beginnings, info_groups_ends


def _extract_info_groups(frame: str) -> list:
    beginnings, ends = _extract_info_groups_positions(frame)
    return [frame[i : j + 1] for (i, j) in zip(beginnings, ends)]


def _verify_frame_list_well_formed(frame: list):
    errors = None
    first_char, last_char = frame[0], frame[-1]

    if first_char != STX:
        error = "First char should be STX but is '{}'".format(first_char)
        errors = _append_error(errors, error)
    if last_char != ETX:
        error = "Last char should be ETX but is '{}'".format(last_char)
        errors = _append_error(errors, error)
    if errors is not None:
        raise FrameFormatError(frame, errors)


def _verify_info_group_well_formed(encoded_info_group: str):
    errors = None
    first_char, last_char = encoded_info_group[:1], encoded_info_group[-1:]
    num_of_sp_sep = encoded_info_group.count(SP)
    num_of_ht_sep = encoded_info_group.count(HT)
    num_of_sep = num_of_sp_sep + num_of_ht_sep

    if first_char != LF:
        error = "First char should be LF but is '{}'".format(first_char.encode())
        errors = _append_error(errors, error)
    if last_char != CR:
        error = "Last char should be CR but is '{}'".format(first_char.encode())
        errors = _append_error(errors, error)
    if num_of_sp_sep > 0 and num_of_ht_sep > 0:
        error = "Should not contain both CR and HT separators"
        errors = _append_error(errors, error)
    if num_of_sep < 2:
        error = "Should contain at least 2 separators but has only '{}'".format(
            num_of_sep
        )
        errors = _append_error(errors, error)
    if errors is not None:
        raise InfoGroupFormatError(encoded_info_group, errors)


def _extract_label_and_data(label_data_and_separators: str) -> (str, str):
    """

    :param label_data_and_separators: str
    :return: label: str
    :return: data: str
    """
    # TODO log info on what the separator is
    # => see issues with separator in data field described on page 18 of
    #    https://www.enedis.fr/sites/default/files/Enedis-NOI-CPT_02E.pdf :
    #
    #  "[..] le champ « étiquette » ne contient aucun caractère ayant une valeur
    #  égale à celle du caractère-séparateur utilisé pour la trame (caractère
    #  ASCII
    #  « espace » ou caractère ASCII « tabulation horizontale » suivant le cas).
    #  Par contre, le champ « donnée » contenant l’information fournie par le groupe
    #  peut, lui, contenir des caractères ayant une valeur égale à celle du
    #  caractère-séparateur utilisé pour la trame."
    #
    # Extracting last separator
    reminder_without_last_sep, sep = (
        label_data_and_separators[:-1],
        label_data_and_separators[-1:],
    )
    # extract label and data
    info_items = reminder_without_last_sep.split(sep)
    label, data_part = info_items[0], info_items[1:]
    # If more than 1 item in the data part, then there was a separator
    # in the data field. In this case, reconstitute the data field
    if len(data_part) > 1:
        # TODO: add a logging info
        data = sep.join(data_part)
    else:
        data = data_part[0]
    return label, data


def _verify_checksum(label_data_and_separators: str, checksum: str):
    checksum_1 = _checksum_method_1(label_data_and_separators)
    checksum_2 = _checksum_method_2(label_data_and_separators)
    if checksum not in (checksum_1, checksum_2):
        raise ChecksumError(
            label_data_and_separators, [checksum, checksum_1, checksum_2]
        )


def _checksum_method_1(label_data_and_separators: str) -> str:
    return _checksum(label_data_and_separators[:-1])


def _checksum_method_2(label_data_and_separators: str) -> str:
    return _checksum(label_data_and_separators)


def _checksum(label_data_and_separators: str) -> str:
    sum_ = 0
    for cks in label_data_and_separators:
        sum_ = sum_ + ord(cks)
    return chr((sum_ & int("111111", 2)) + 0x20)
