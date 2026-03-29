# pyteleinfo

A Python library for decoding and encoding ENEDIS teleinfo frames - implementation of the
tele-information communication frames specifications for French electronic electricity meters.

[![PyPI version](https://badge.fury.io/py/pyteleinfo.svg)](https://badge.fury.io/py/pyteleinfo)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyteleinfo.svg)](https://pypi.org/project/pyteleinfo/)

## Features

- **Decode teleinfo frames** from French ENEDIS electricity meters
- **Encode data** back to teleinfo format
- **Read frames from serial port** with configurable settings
- **Async I/O support** with pyserial-asyncio
- Comprehensive **exception handling**
- **Pydantic-based settings** with environment variable support

## Installation

```bash
pip install pyteleinfo
```

## Quick Start

### Decoding Teleinfo Frames

```python
from teleinfo import decode

# Decode a raw teleinfo frame (bytes or string)
raw_frame = b'\x02\nADCO 050022120078 2\r\nOPTARIF HC.. <\r\x03'
decoded = decode(raw_frame)
print(decoded)
# [{'label': 'ADCO', 'data': '050022120078'}, {'label': 'OPTARIF', 'data': 'HC..'}]
```

### Reading from a Serial Port

```python
from teleinfo import read_frame, decode

# Read a complete frame from the serial port
raw = read_frame("/dev/ttyUSB0")
decoded = decode(raw)
print(decoded)
```

Settings can be customized via the `TeleinfoSettings` class or environment variables
(prefixed with `TELEINFO_`, e.g. `TELEINFO_BAUDRATE=1200`):

```python
from teleinfo.settings import TeleinfoSettings

settings = TeleinfoSettings(baudrate=9600, timeout=10.0)
raw = read_frame("/dev/ttyUSB0", settings=settings)
```

## Requirements

- Python >= 3.12
- pyserial >= 3.5
- pyserial-asyncio >= 0.6
- pydantic-settings >= 2.13.1

## Development

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/esciara/pyteleinfo.git
cd pyteleinfo
uv sync --group dev

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src
```

## License

BSD 3-Clause License - Copyright (c) 2019 Emmanuel Sciara

See [LICENSE](LICENSE) file for details.

## Links

- **GitHub Repository**: [esciara/pyteleinfo](https://github.com/esciara/pyteleinfo)
- **PyPI Package**: [pyteleinfo](https://pypi.org/project/pyteleinfo)
- **Issue Tracker**: [GitHub Issues](https://github.com/esciara/pyteleinfo/issues)
