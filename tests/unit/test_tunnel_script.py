"""scripts/tunnel.sh holds no credential and stops the tunnel on exit (story 4.2)."""

import re
import subprocess

from tests.target import REPO

SCRIPT = REPO / "scripts" / "tunnel.sh"


def test_the_script_commits_no_credential() -> None:
    text = SCRIPT.read_text()
    assert "NGROK_AUTHTOKEN:-" in text and "ngrok config check" in text
    assert not re.search(r"authtoken[= ]+['\"]?[A-Za-z0-9_]{20,}", text, re.IGNORECASE)
    assert not re.search(r"\b\d[A-Za-z0-9]{20,}_[A-Za-z0-9]{20,}\b", text)  # ngrok token shape


def test_the_tunnel_stops_when_the_script_exits() -> None:
    text = SCRIPT.read_text()
    assert "trap cleanup EXIT" in text and 'kill "$PID"' in text


def test_the_host_header_is_not_rewritten() -> None:
    assert "host-header" not in SCRIPT.read_text().lower()


def test_it_refuses_to_run_without_a_hostname() -> None:
    result = subprocess.run(
        ["bash", str(SCRIPT)], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}
    )
    assert result.returncode != 0 and "TUNNEL_HOSTNAME" in result.stderr
