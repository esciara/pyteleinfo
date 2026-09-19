# Task: migration to serialx - actual implementation

Repository: `esciara/pyteleinfo` (Python >= 3.12, sources in `src/teleinfo`, hatchling build,
uv-managed). Work on the branch the session is assigned to. Do not open a pull request.

## Goal

Make the serialx migration specified in `.claude/tasks/serialx-migration.md` complete and
proven. Commit `70107c1` ("feat!: replace pyserial and pyserial-asyncio-fast with serialx, bump
version to 0.5.0") already landed on `main` and is the starting point of this branch. This task:

1. Audits the current code against every requirement of the specification (kwargs, exception
   handling order, single open per port, bounded async reads, first-frame discard, `raw` output,
   docs wording, test coverage listed there).
2. Implements whatever is missing or wrong. Do not rewrite what already matches the spec.
3. Proves the result with the acceptance commands and the end-to-end PTY behaviour below.

Use **uv for everything**: `uv sync --group dev`, `uv run pytest`, `uv run ruff`,
`uv run mypy`, `uv run mkdocs build --strict`, `uv run python -m teleinfo`. Never call pip
directly. Do not change the dependency set or the version unless a spec requirement demands it.

## Verified facts (do not re-derive)

- `pyproject.toml` depends on `serialx>=1.10.0`; `uv.lock` pins serialx 1.10.0 and contains no
  pyserial entry. `src/teleinfo/__version__.py` and `pyproject.toml` both say `0.5.0`.
- `src/teleinfo/settings.py`, `src/teleinfo/serial_reader.py` and
  `src/teleinfo/console/commands.py` already import `serialx`; `commands.py` has an
  `_open_port(port, settings) -> serialx.AsyncSerial` helper and uses
  `serialx.async_list_serial_ports()` for discovery.
- `tests/teleinfo/test_commands.py` and `tests/teleinfo/test_serial_reader.py` exist and were
  written for serialx in commit `70107c1`.
- All serialx behaviour facts in `.claude/tasks/serialx-migration.md` still hold: sync
  `serial_for_url(..., byte_size=, read_timeout=, rtscts=)` as a context manager with
  `read(1) -> b""` on timeout; async `async_serial_for_url(...)` with `readuntil`; constants
  `SEVENBITS`, `PARITY_EVEN`, `STOPBITS_ONE`; exceptions `FileNotFoundError` / `OSError` /
  `TimeoutError` (a subclass of `OSError`, so it must be caught first); ports open exclusively;
  `read_timeout` is ignored by async `readuntil`, so every async read must be wrapped in
  `asyncio.wait_for(..., timeout=settings.timeout)`; closing mid-read raises
  `asyncio.IncompleteReadError`; `loop://` is not usable on Linux, so tests mock the port.
- pytest-asyncio runs in strict mode: async tests need `@pytest.mark.asyncio`.
- Never add `serialx-compat`.

## Files to touch

Only where the audit finds a gap against the specification:

- `src/teleinfo/settings.py`, `src/teleinfo/serial_reader.py`,
  `src/teleinfo/console/commands.py`
- `tests/teleinfo/test_serial_reader.py`, `tests/teleinfo/test_commands.py`
- `README.md`, `docs/index.md`
- `pyproject.toml`, `uv.lock`, `src/teleinfo/__version__.py` only if a spec requirement forces it

Do not touch `codec.py`, `.bumpversion.cfg`, `justfile`, `tox` configuration, or CI files.

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
frames and exits 0. Repeat once with `--raw` and confirm the two frames are printed as Python
`bytes` reprs. Do not reopen the same PTY slave twice in one process; some sandboxes return
EINVAL from `tcsetattr` on a reopened slave and that is not a library bug.

## Pre-existing issues, out of scope

Leave these alone and mention them in the summary: two `B905` ruff findings in `codec.py`,
`just lint` failing because `tox-pyenv` no longer imports against current tox, and
`.bumpversion.cfg` being stale.

## Deliverable

If the audit finds gaps: one commit with a descriptive message listing each gap closed, pushed
to the assigned branch. If the audit finds no gaps and every check passes: no commit, and the
report says so explicitly. Either way: a summary of what was audited and changed, the
verification results as a table with the verifier's real output for the acceptance commands and
the PTY run, and anything left out.
