# Task: migrate pyteleinfo from pyserial / pyserial-asyncio-fast to serialx

Repository: `esciara/pyteleinfo` (Python >= 3.12, sources in `src/teleinfo`, hatchling build,
uv-managed). Work on the branch the session is assigned to. Do not open a pull request.

## Goal

Replace the `pyserial` + `pyserial-asyncio-fast` dependency pair with `serialx`
(https://pypi.org/project/serialx/, >= 1.10.0), keeping the sync `read_frame` API and the async
CLI (`teleinfo port <device>` and `teleinfo discover`) working. Bump the version (minor, since
exception types change).

Use **uv for everything**: `uv remove`, `uv add`, `uv lock`, `uv sync --group dev`,
`uv run pytest`, `uv run ruff`, `uv run mypy`, `uv run mkdocs build --strict`,
`uv run python -m teleinfo`. Never call pip directly.

## Verified facts about serialx (do not re-derive)

- No dependency on pyserial. Pure Python on Linux. Ships `py.typed`.
- Sync API: `serialx.serial_for_url(port, baudrate=, byte_size=, parity=, stopbits=, rtscts=,
  read_timeout=)` used as a context manager. `ser.read(1)` returns `b""` on timeout, exactly
  like pyserial, so the sync reader loop can stay as is.
- Async API: `serialx.async_serial_for_url(port, baudrate=, byte_size=, parity=, stopbits=,
  rtscts=)` used with `async with`; the object has `readuntil(separator)`, `readexactly`,
  `readline`, `write`, `is_open`. A `(StreamReader, StreamWriter)` pair is also available via
  `serialx.open_serial_connection(url=..., ...)`.
- Constants `serialx.SEVENBITS` (int 7), `serialx.PARITY_EVEN` (str enum "E"),
  `serialx.STOPBITS_ONE` (float enum 1.0) exist under the same names as pyserial.
- Kwarg renames vs pyserial: `bytesize` -> `byte_size` (old name still accepted as alias),
  `timeout` -> `read_timeout`, `rtscts` is a bool.
- Exceptions: missing device raises `FileNotFoundError`, I/O errors raise `OSError`, timeouts
  raise `TimeoutError`. There is no `SerialException` to catch in normal flows. `termios.error`
  can still surface from port configuration and is NOT an `OSError` subclass.
- **`TimeoutError` is a subclass of `OSError`.** Any `except TimeoutError` branch must come
  before an `except OSError` branch.
- **Ports open exclusively by default** (`exclusive=True`, flock). Opening the same device
  twice in one process fails. The current CLI reopens the port for every frame and never closes
  it, so it must be restructured to open once per port, discard the first (probably partial)
  frame, then read `max_frames` frames from the same connection, then close.
- The `read_timeout` kwarg is ignored by the async `readuntil`. Bound every async read with
  `asyncio.wait_for(..., timeout=settings.timeout)`.
- Port closing mid-read raises `asyncio.IncompleteReadError`; treat it as a port error in the CLI.
- Port enumeration: `serialx.list_serial_ports()` / `await serialx.async_list_serial_ports()`
  return objects with a `.device` attribute, replacing `serial.tools.list_ports.comports()`.
- `loop://` is documented but not registered on Linux in 1.10.0; tests must mock the port.
- Never add `serialx-compat`; it shadows the `serial` import path and raises at import time
  when pyserial is also installed.

## Files to touch

- `pyproject.toml`, `uv.lock` (dependency swap, version bump), `src/teleinfo/__version__.py`
- `src/teleinfo/settings.py`: constants from serialx; keep field names `bytesize`, `parity`,
  `stopbits`, `rtscts`, `timeout`, `max_frames` so `TELEINFO_*` env vars keep working;
  `rtscts` becomes `bool` default `True`.
- `src/teleinfo/serial_reader.py`: sync reader; update the docstring `Raises` section.
- `src/teleinfo/console/commands.py`: restructured async CLI as described above; keep the
  printed messages; the `raw` flag output must be `f"{frame!r}"` to satisfy mypy
  `str-bytes-safe`.
- `tests/teleinfo/test_serial_reader.py`: patch `teleinfo.serial_reader.serialx.serial_for_url`;
  assert call kwargs `byte_size`, `read_timeout`, `rtscts=True`; replace the `SerialException`
  propagation test with a `FileNotFoundError` one.
- New `tests/teleinfo/test_commands.py`: mock `teleinfo.console.commands.serialx.async_serial_for_url`
  as an async context manager (`__aenter__`/`__aexit__` as `AsyncMock`) and cover: single open
  with first frame discarded and `max_frames` decoded, raw output, missing device -> returns
  False with stderr message, timeout -> prints "Timeout!", `IncompleteReadError` -> False,
  invalid frame -> False, and `async_receive_frame` raising `TimeoutError` via `wait_for`.
  pytest-asyncio is in strict mode, so mark tests with `@pytest.mark.asyncio`.
- `README.md` and `docs/index.md`: replace the pyserial mentions, list `serialx >= 1.10.0`,
  add a sentence on the new exception types.

## Acceptance commands

All must pass, in this order, and their real output must be reported:

```bash
uv sync --group dev
uv run pytest -q tests
uv run ruff check --select I src/teleinfo tests
uv run ruff format --check src/teleinfo tests
uv run mypy -p teleinfo -p tests
uv run mkdocs build --strict -q
uv run python -m teleinfo port /dev/ttyNOPE   # expect a clean "Error reading port" line, exit 0
```

## Acceptance behaviour (end-to-end)

From a throwaway Python script in the scratchpad directory: open a PTY pair with
`pty.openpty()`, start `uv run python -m teleinfo port <slave>` with `TELEINFO_TIMEOUT=3` and
`TELEINFO_MAX_FRAMES=2`, wait about 2.5 s, write the tail of a partial frame followed by three
complete Linky frames from the master side, and confirm the CLI prints exactly two decoded JSON
frames and exits 0. Do not reopen the same PTY slave twice in one process; some sandboxes return
EINVAL from `tcsetattr` on a reopened slave and that is not a library bug.

## Pre-existing issues, out of scope

Leave these alone and mention them in the summary: two `B905` ruff findings in `codec.py`,
`just lint` failing because `tox-pyenv` no longer imports against current tox, and
`.bumpversion.cfg` being stale (bump the two version strings directly).

## Deliverable

One commit with a descriptive message explaining the dependency swap, the exception change, and
why the CLI now opens the port once. Pushed to the assigned branch. A summary of what changed,
the verification results as a table, and anything left out.
