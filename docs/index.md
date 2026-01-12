# pyteleinfo Documentation

A serial reader for ENEDIS teleinfo - implementation of the tele-information
communication frames specifications for French electronic electricity meters.

## Overview

pyteleinfo provides functions to decode/encode teleinfo data strings to/from JSON format,
supporting both string and bytes data, async I/O operations, and both historical and standard
teleinfo modes.

## Features

- Decode teleinfo frames from French ENEDIS electricity meters
- Encode data back to teleinfo format
- Support for both historical and standard modes
- Async I/O support with pyserial-asyncio
- Command-line interface for reading teleinfo data
- Comprehensive exception handling

## Installation

Install from PyPI:

```bash
pip install pyteleinfo
```

## Quick Start

### Reading Teleinfo Data

```python
from teleinfo.codec import decode_frame

# Decode a raw teleinfo frame
raw_frame = b'\x02ADCO 123456789012 A\r\nOPTARIF HC.. <\r\n\x03'
decoded = decode_frame(raw_frame)
print(decoded)
# Output: JSON representation of the teleinfo data
```

### Command Line Usage

Read teleinfo data directly from a serial port:

```bash
# Read from serial port
teleinfo read /dev/ttyUSB0

# With specific mode
teleinfo read /dev/ttyUSB0 --mode standard
```

## Documentation Sections

- **[API Reference](reference/)** - Complete API documentation for all modules

## Links

- **GitHub**: [esciara/pyteleinfo](https://github.com/esciara/pyteleinfo)
- **PyPI**: [pyteleinfo](https://pypi.org/project/pyteleinfo)
- **Issues**: [GitHub Issues](https://github.com/esciara/pyteleinfo/issues)

## License

BSD License - Copyright © 2019 Emmanuel Sciara
