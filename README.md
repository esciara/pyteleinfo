# pyteleinfo

A serial reader for ENEDIS teleinfo - implementation of the tele-information
communication frames specifications for French electronic electricity meters.

[![PyPI version](https://badge.fury.io/py/pyteleinfo.svg)](https://badge.fury.io/py/pyteleinfo)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyteleinfo.svg)](https://pypi.org/project/pyteleinfo/)

## Features

- **Decode teleinfo frames** from French ENEDIS electricity meters
- **Encode data** back to teleinfo format
- Support for both **historical and standard modes**
- **Async I/O support** with pyserial-asyncio
- **Command-line interface** for reading teleinfo data
- Comprehensive **exception handling**
- Full **type hints** support

## Installation

Install from PyPI:

```bash
pip install pyteleinfo
```

For development:

```bash
git clone https://github.com/esciara/pyteleinfo.git
cd pyteleinfo
uv sync --extra dev
```

## Quick Start

### Decoding Teleinfo Frames

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

### Async I/O

```python
import asyncio
from teleinfo.codec import decode_frame

async def read_teleinfo(port):
    # Your async code here
    pass

asyncio.run(read_teleinfo('/dev/ttyUSB0'))
```

## Documentation

Full documentation is available at: [pyteleinfo documentation](https://pyteleinfo.readthedocs.io/)

## Requirements

- Python >= 3.12
- pyserial >= 3.5
- pyserial-asyncio >= 0.6
- cleo >= 0.8

## Development

### Setup Development Environment

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/esciara/pyteleinfo.git
cd pyteleinfo
uv sync --extra dev
```

### Running Tests

```bash
# Run all tests
just test

# Run with tox
just tox
```

### Building Documentation

```bash
# Build documentation
just docs

# Serve documentation locally
just docs-serve
```

### Code Quality

```bash
# Format code
just format

# Lint code
just lint

# Type checking
just type
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

BSD License - Copyright © 2019 Emmanuel Sciara

See [LICENSE](LICENSE) file for details.

## Links

- **GitHub Repository**: [esciara/pyteleinfo](https://github.com/esciara/pyteleinfo)
- **PyPI Package**: [pyteleinfo](https://pypi.org/project/pyteleinfo)
- **Issue Tracker**: [GitHub Issues](https://github.com/esciara/pyteleinfo/issues)
- **Documentation**: [Read the Docs](https://pyteleinfo.readthedocs.io/)

## Acknowledgments

This project implements the teleinfo protocol specification for French electronic electricity meters as defined by ENEDIS.
