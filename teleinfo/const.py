"""
Package constants
"""

#: Teleinfo specification base encoding.
ENCODING = "ascii"
#: NULL BIT
NULL = "\x00"
#: Start of TeXt token.
STX = "\x02"
#: End of TeXt token.
ETX = "\x03"
#: SPace token.
SP = "\x20"
#: Horizontal Tab token.
# HT = "\x09"
HT = "\t"
#: End Of Transmission token.
EOT = "\x04"
#: Message chunk end token.
LF = "\n"
CR = "\r"

# Dict keys for info groups
LABEL = "label"
DATA = "data"
CHECKSUM = "checksum"
