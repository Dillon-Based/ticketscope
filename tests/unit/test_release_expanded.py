"""Expanded coverage for `fetch_snapshot` (story 5): pin normalisation, a missing
destination folder, and the digests a refused local asset reports."""

import hashlib
from pathlib import Path

import httpx2
import pytest

from ticketscope.adapters.release import ChecksumMismatch, asset_name, fetch_snapshot, sha256_file

BASE = "https://example.invalid/download"
VERSION = "2026.11.1"
BODY = b"pretend gzip bytes" * 100
SHA = hashlib.sha256(BODY).hexdigest()


def _ok() -> httpx2.MockTransport:
    return httpx2.MockTransport(lambda r: httpx2.Response(200, content=BODY))


def test_pin_with_surrounding_whitespace_is_accepted(tmp_path: Path) -> None:
    path = fetch_snapshot(BASE, VERSION, tmp_path, f"  {SHA}\n", timeout=5, transport=_ok())
    assert path.read_bytes() == BODY


def test_missing_destination_folder_is_created(tmp_path: Path) -> None:
    dest = tmp_path / "a" / "b"
    path = fetch_snapshot(BASE, VERSION, dest, SHA, timeout=5, transport=_ok())
    assert path == dest / asset_name(VERSION)
    assert path.is_file()


def test_refused_local_asset_reports_both_digests(tmp_path: Path) -> None:
    local = tmp_path / asset_name(VERSION)
    local.write_bytes(b"other")
    with pytest.raises(ChecksumMismatch) as caught:
        fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=_ok())
    assert caught.value.expected == SHA
    assert caught.value.actual == hashlib.sha256(b"other").hexdigest()
    assert str(local) in str(caught.value)


def test_second_fetch_reuses_the_verified_download(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(str(request.url))
        return httpx2.Response(200, content=BODY)

    transport = httpx2.MockTransport(handler)
    first = fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=transport)
    second = fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=transport)
    assert first == second
    assert len(calls) == 1


def test_sha256_file_matches_hashlib_across_chunk_boundaries(tmp_path: Path) -> None:
    data = b"x" * ((1 << 20) + 7)
    path = tmp_path / "big"
    path.write_bytes(data)
    assert sha256_file(path) == hashlib.sha256(data).hexdigest()
