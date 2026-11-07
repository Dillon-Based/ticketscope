"""`fetch_snapshot`: checksum verification, the local-file path and partial-file cleanup."""

import hashlib
from collections.abc import Callable
from pathlib import Path

import httpx2
import pytest

from ticketscope.adapters.release import ChecksumMismatch, asset_url, fetch_snapshot

BASE = "https://example.invalid/download"
VERSION = "2026.11.1"
BODY = b"\x1f\x8b pretend gzip bytes" * 1000
SHA = hashlib.sha256(BODY).hexdigest()


def _transport(
    handler: Callable[[httpx2.Request], httpx2.Response], seen: list[str] | None = None
) -> httpx2.MockTransport:
    def record(request: httpx2.Request) -> httpx2.Response:
        if seen is not None:
            seen.append(str(request.url))
        return handler(request)

    return httpx2.MockTransport(record)


def test_asset_url_names_the_release_tag_and_asset() -> None:
    assert asset_url(BASE + "/", VERSION) == f"{BASE}/snapshot-{VERSION}/{VERSION}.jsonl.gz"


def test_download_with_the_pinned_checksum_is_kept(tmp_path: Path) -> None:
    seen: list[str] = []
    transport = _transport(lambda r: httpx2.Response(200, content=BODY), seen)
    path = fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=transport)
    assert path == tmp_path / f"{VERSION}.jsonl.gz"
    assert path.read_bytes() == BODY
    assert seen == [asset_url(BASE, VERSION)]
    assert [p.name for p in tmp_path.iterdir()] == [path.name]


def test_download_follows_the_release_redirect(tmp_path: Path) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.host == "objects.example.invalid":
            return httpx2.Response(200, content=BODY)
        return httpx2.Response(302, headers={"Location": "https://objects.example.invalid/a"})

    path = fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=_transport(handler))
    assert path.read_bytes() == BODY


def test_checksum_mismatch_deletes_the_download(tmp_path: Path) -> None:
    transport = _transport(lambda r: httpx2.Response(200, content=b"tampered"))
    with pytest.raises(ChecksumMismatch) as caught:
        fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=transport)
    assert caught.value.expected == SHA
    assert caught.value.actual == hashlib.sha256(b"tampered").hexdigest()
    assert SHA in str(caught.value) and caught.value.actual in str(caught.value)
    assert list(tmp_path.iterdir()) == []


def test_pin_is_compared_case_insensitively(tmp_path: Path) -> None:
    transport = _transport(lambda r: httpx2.Response(200, content=BODY))
    path = fetch_snapshot(BASE, VERSION, tmp_path, SHA.upper(), timeout=5, transport=transport)
    assert path == tmp_path / f"{VERSION}.jsonl.gz"
    assert path.read_bytes() == BODY


def test_http_error_leaves_no_partial_file(tmp_path: Path) -> None:
    transport = _transport(lambda r: httpx2.Response(404, content=b"not found"))
    with pytest.raises(httpx2.HTTPStatusError):
        fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=transport)
    assert list(tmp_path.iterdir()) == []


def test_interrupted_stream_leaves_no_partial_file(tmp_path: Path) -> None:
    class Broken(httpx2.SyncByteStream):
        def __iter__(self):  # type: ignore[override]
            yield BODY[:100]
            raise httpx2.ReadError("connection reset")

    transport = _transport(lambda r: httpx2.Response(200, stream=Broken()))
    with pytest.raises(httpx2.ReadError):
        fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=transport)
    assert list(tmp_path.iterdir()) == []


def test_timeout_leaves_no_partial_file(tmp_path: Path) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectTimeout("timed out", request=request)

    with pytest.raises(httpx2.ConnectTimeout):
        fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=_transport(handler))
    assert list(tmp_path.iterdir()) == []


def test_local_file_with_the_pin_is_used_without_downloading(tmp_path: Path) -> None:
    local = tmp_path / f"{VERSION}.jsonl.gz"
    local.write_bytes(BODY)

    def handler(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("downloaded although a local asset exists")

    path = fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5, transport=_transport(handler))
    assert path == local


def test_local_file_with_another_checksum_is_refused_and_kept(tmp_path: Path) -> None:
    local = tmp_path / f"{VERSION}.jsonl.gz"
    local.write_bytes(b"other bytes")
    with pytest.raises(ChecksumMismatch):
        fetch_snapshot(BASE, VERSION, tmp_path, SHA, timeout=5)
    assert local.read_bytes() == b"other bytes"


@pytest.mark.parametrize("pin", ["", "   "])
def test_empty_pin_is_refused_before_any_request(tmp_path: Path, pin: str) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("requested with no pin")

    with pytest.raises(ValueError, match="TICKETSCOPE_SNAPSHOT_SHA256"):
        fetch_snapshot(BASE, VERSION, tmp_path, pin, timeout=5, transport=_transport(handler))
    assert list(tmp_path.iterdir()) == []
