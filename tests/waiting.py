"""Bounded eventual assertions and observable subprocess output for cluster checks."""

import os
import selectors
import subprocess
import time
from collections.abc import Callable
from threading import Event

_WAIT = Event().wait


def eventually[T](
    check: Callable[[], T],
    *,
    timeout: float,
    interval: float,
    clock: Callable[[], float] = time.monotonic,
    wait: Callable[[float], object] = _WAIT,
) -> T:
    """Retry assertion failures only; preserve the final diagnostic at the deadline.

    Tempo has no push notification for complete ingestion, so its assertion uses an
    explicit retry policy. Probe immediately and never wait beyond the remaining budget.
    """
    if timeout < 0 or interval <= 0:
        raise ValueError("timeout must be nonnegative and interval positive")
    deadline = clock() + timeout
    while True:
        try:
            return check()
        except AssertionError:
            remaining = deadline - clock()
            if remaining <= 0:
                raise
            wait(min(interval, remaining))


def wait_for_output(
    process: subprocess.Popen[bytes],
    accept: Callable[[str], bool],
    *,
    timeout: float,
) -> str:
    """Read complete lines as they arrive, with EOF and a bounded deadline.

    The caller owns process termination. stdout and stderr should be merged so
    early startup errors are available in the failure diagnostic.
    """
    assert process.stdout is not None
    deadline = time.monotonic() + timeout
    pending = b""
    observed: list[str] = []
    with selectors.DefaultSelector() as ready:
        ready.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            assert remaining > 0, f"output not ready in {timeout}s: {observed}"
            assert ready.select(remaining), f"output not ready in {timeout}s: {observed}"
            chunk = os.read(process.stdout.fileno(), 65536)
            assert chunk, f"process closed output before readiness: {observed}"
            pending += chunk
            while b"\n" in pending:
                raw, pending = pending.split(b"\n", 1)
                line = raw.decode(errors="replace").strip()
                observed.append(line)
                if accept(line):
                    return line
