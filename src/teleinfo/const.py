"""
Package constants
"""

#: Teleinfo specification base encoding.
ENCODING = "ascii"
#: NULL BIT
NULL = "\x00"
#: Start of TeXt token.
STX_TOKEN = "\x02"
#: End of TeXt token.
ETX_TOKEN = "\x03"
#: SPace token.
SP_TOKEN = "\x20"
#: Horizontal Tab token.
# HT = "\x09"
HT_TOKEN = "\t"
#: End Of Transmission token.
EOT_TOKEN = "\x04"
#: Message chunk end token.
LF_TOKEN = "\n"
CR_TOKEN = "\r"

# Dict keys for info groups
LABEL_KEY = "label"
DATA_KEY = "data"
CHECKSUM_KEY = "checksum"
