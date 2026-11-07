"""[P1] Waiting policy fails on genuine faults and preserves deadline diagnostics."""

import subprocess
import sys

import pytest

from tests.waiting import eventually, wait_for_output


def test_eventual_assertion_retries_and_returns_the_success_value() -> None:
    attempts = 0
    waits: list[float] = []

    def check() -> str:
        nonlocal attempts
        attempts += 1
        assert attempts == 3, "not yet"
        return "complete"

    assert (
        eventually(check, timeout=3, interval=1, clock=lambda: 0, wait=waits.append) == "complete"
    )
    assert attempts == 3
    assert waits == [1, 1]


def test_eventual_assertion_caps_wait_and_preserves_last_failure() -> None:
    now = 0.0
    waits: list[float] = []

    def wait(delay: float) -> None:
        nonlocal now
        waits.append(delay)
        now += delay

    def check() -> None:
        raise AssertionError(f"last observation at {now}")

    with pytest.raises(AssertionError, match=r"last observation at 2\.5"):
        eventually(check, timeout=2.5, interval=2, clock=lambda: now, wait=wait)
    assert waits == [2, 0.5]


def test_eventual_assertion_does_not_retry_programming_errors() -> None:
    def check() -> None:
        raise TypeError("bad probe")

    with pytest.raises(TypeError, match="bad probe"):
        eventually(check, timeout=10, interval=1, wait=lambda _: pytest.fail("unexpected wait"))


def test_process_readiness_uses_output_including_multiple_lines_in_one_write() -> None:
    with subprocess.Popen(
        [sys.executable, "-c", "print('starting\\nForwarding from 127.0.0.1:1234 -> 80')"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ) as process:
        line = wait_for_output(process, lambda line: line.startswith("Forwarding from"), timeout=5)
    assert line == "Forwarding from 127.0.0.1:1234 -> 80"


def test_process_exit_reports_last_output_instead_of_waiting_for_deadline() -> None:
    with (
        subprocess.Popen(
            [sys.executable, "-c", "print('address already in use')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as process,
        pytest.raises(AssertionError, match="address already in use"),
    ):
        wait_for_output(process, lambda line: line.startswith("Forwarding from"), timeout=5)
