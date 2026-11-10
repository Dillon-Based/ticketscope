"""The embedding asset: a gzipped JSONL of vectors, built by a person and loaded by `load`.

Line 1 is the manifest. Every later line is one record holding only the issue number, the
model id and the vector (Provenance: no text, key, URL or author). The file is gzipped and
checksummed as a whole, so the manifest is covered by the pin.
"""

import gzip
import json
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AssetManifest(_Strict):
    """What the asset was built from, and how many vectors of which size it holds."""

    snapshot: str
    model_id: str
    model_sha256: str
    preprocessing_version: str
    runtime: dict[str, str]
    dimension: int = Field(gt=0)
    count: int = Field(ge=0)

    def mismatch(self, *, snapshot: str, model_id: str, preprocessing_version: str) -> str | None:
        """Why this asset is not the one the pin names, or `None`."""
        wanted = {
            "snapshot": snapshot,
            "model_id": model_id,
            "preprocessing_version": preprocessing_version,
        }
        problems = [
            f"manifest {field} {getattr(self, field)!r}, expected {value!r}"
            for field, value in wanted.items()
            if getattr(self, field) != value
        ]
        return "; ".join(problems) or None


class AssetRecord(_Strict):
    issue: int
    model: str
    vector: list[float]

    @classmethod
    def parse(cls, line: str) -> Self:
        return cls.model_validate_json(line)


def _vector_json(vector: Sequence[float]) -> str:
    # Nine significant digits round-trip a float32, which is what the model produces.
    return "[" + ",".join(f"{x:.9g}" for x in vector) + "]"


def record_line(issue: int, model_id: str, vector: Sequence[float]) -> str:
    return f'{{"issue":{issue},"model":{json.dumps(model_id)},"vector":{_vector_json(vector)}}}'


def write_asset(
    path: Path, manifest: AssetManifest, records: Iterable[tuple[int, str, Sequence[float]]]
) -> int:
    """Write the manifest, then each record; returns the number of records written."""
    written = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as out:
        out.write(manifest.model_dump_json() + "\n")
        for issue, model_id, vector in records:
            out.write(record_line(issue, model_id, vector) + "\n")
            written += 1
    return written


def read_manifest(path: Path) -> AssetManifest:
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        return AssetManifest.model_validate_json(lines.readline())


def read_records(path: Path) -> Iterator[AssetRecord]:
    """Yield each record after the manifest, validating every line."""
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        next(lines, None)
        for lineno, line in enumerate(lines, start=2):
            if not line.strip():
                continue
            try:
                yield AssetRecord.parse(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: invalid embedding record: {exc}") from exc
