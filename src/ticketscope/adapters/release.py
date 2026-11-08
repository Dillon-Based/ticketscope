"""Release adapter: fetch a pinned snapshot asset and verify its checksum (AD-6).

The asset lives at `{base_url}/snapshot-{version}/{version}.jsonl.gz`. A local copy at
`<dest_dir>/<version>.jsonl.gz` is used if present; it is checked against the same pin.
"""

import hashlib
import logging
import os
import re
import tempfile
from pathlib import Path

import httpx2

log = logging.getLogger(__name__)

_CHUNK = 1 << 20

_SNAPSHOT_BLOCK = re.compile(r"^snapshot:\n((?:[ \t]+.*\n|[ \t]*#.*\n|\n)+)", re.MULTILINE)
_PIN_FIELD = re.compile(
    r'^[ \t]+(version|sha256|baseUrl):[ \t]*"?([^"\n#]*?)"?[ \t]*$', re.MULTILINE
)


def read_snapshot_pin(values: Path) -> dict[str, str]:
    """`snapshot.version`, `sha256` and `baseUrl` from a chart's values.yaml (no YAML
    dependency: the block is flat)."""
    block = _SNAPSHOT_BLOCK.search(values.read_text(encoding="utf-8"))
    if block is None:
        raise ValueError(f"{values}: no top-level snapshot: block")
    pin = dict(_PIN_FIELD.findall(block.group(1)))
    missing = {"version", "sha256", "baseUrl"} - set(pin)
    if missing:
        raise ValueError(f"{values}: snapshot block lacks {sorted(missing)}")
    return pin


class ChecksumMismatch(ValueError):
    """The asset's SHA-256 is not the pinned one."""

    def __init__(self, path: Path | str, expected: str, actual: str) -> None:
        super().__init__(f"{path}: SHA-256 {actual} does not match the pinned {expected}")
        self.expected = expected
        self.actual = actual


def asset_name(version: str) -> str:
    return f"{version}.jsonl.gz"


def asset_url(base_url: str, version: str) -> str:
    return f"{base_url.rstrip('/')}/snapshot-{version}/{asset_name(version)}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_snapshot(
    base_url: str,
    version: str,
    dest_dir: Path,
    sha256: str,
    *,
    timeout: float,
    transport: httpx2.BaseTransport | None = None,
) -> Path:
    """Return the path of the verified asset `<dest_dir>/<version>.jsonl.gz`.

    Raises `ValueError` on an empty pin, `ChecksumMismatch` when the bytes differ from
    it (a downloaded file is then deleted; a local one is left alone), and
    `httpx2.HTTPError` when the download fails. No partial file is left behind.
    """
    expected = sha256.strip().lower()
    if not expected:
        raise ValueError("TICKETSCOPE_SNAPSHOT_SHA256 is empty; the snapshot pin needs a checksum")
    dest = dest_dir / asset_name(version)
    if dest.is_file():
        actual = sha256_file(dest)
        if actual != expected:
            raise ChecksumMismatch(dest, expected, actual)
        log.info("using local snapshot %s (checksum verified)", dest)
        return dest

    dest_dir.mkdir(parents=True, exist_ok=True)
    url = asset_url(base_url, version)
    log.info("downloading %s", url)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{asset_name(version)}.", dir=dest_dir)
    tmp = Path(tmp_name)
    try:
        digest = hashlib.sha256()
        with (
            os.fdopen(fd, "wb") as out,
            httpx2.Client(follow_redirects=True, timeout=timeout, transport=transport) as client,
            client.stream("GET", url) as response,
        ):
            response.raise_for_status()
            for chunk in response.iter_bytes(_CHUNK):
                digest.update(chunk)
                out.write(chunk)
        actual = digest.hexdigest()
        if actual != expected:
            raise ChecksumMismatch(url, expected, actual)
        tmp.replace(dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    log.info("downloaded %s (checksum verified)", dest)
    return dest
