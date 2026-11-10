"""The `Embedder` adapters: fastembed over the baked ONNX model, and a traced wrapper.

The model is read from a local cache only (it is baked into the image, and the runtime is
offline). `core` never imports this: the `embeddings {model}` span is emitted here (AD-1,
AD-10).
"""

import hashlib
import os
import sys
from collections.abc import Generator, Iterable, Sequence
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Protocol, cast

from opentelemetry.trace import Tracer

from ticketscope import telemetry
from ticketscope.core.ports import Embedder


class _Vector(Protocol):
    def tolist(self) -> list[float]: ...


class _TextModel(Protocol):
    def embed(self, documents: Iterable[str], **kwargs: Any) -> Iterable[_Vector]: ...


@contextmanager
def _native_output_silenced() -> Generator[None]:
    """Send file descriptors 1 and 2 to /dev/null for the block.

    onnxruntime writes its start-up warnings (device discovery, telemetry) from C++ straight
    to the process's stdout, as coloured non-JSON lines, and the api's logs are JSON lines.
    Python exceptions still propagate; only the native output is dropped.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    saved = (os.dup(1), os.dup(2))
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        for fd in (*saved, devnull):
            os.close(fd)


class FastEmbedEmbedder:
    """`Embedder` over fastembed's `TextEmbedding`. Loading the model is eager."""

    def __init__(self, model_id: str, cache_dir: Path) -> None:
        self.model_id = model_id
        with _native_output_silenced():
            # Imported here: jobs and tests that never embed do not load onnxruntime.
            import onnxruntime  # pyright: ignore[reportMissingTypeStubs]
            from fastembed import TextEmbedding  # pyright: ignore[reportMissingTypeStubs]

            cast(Any, onnxruntime).set_default_logger_severity(3)
            factory = cast(Any, TextEmbedding)
            self._model = cast(_TextModel, factory(model_name=model_id, cache_dir=str(cache_dir)))
        self._inference_lock = Lock()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        # fastembed returns a lazy iterable. Keep the model's inference workspace
        # exclusive until every vector has been materialized, including tolist().
        with self._inference_lock:
            return [vector.tolist() for vector in self._model.embed(list(texts))]


class TracedEmbedder:
    """Wraps an `Embedder` so each call is one `embeddings {model}` span."""

    def __init__(self, inner: Embedder, tracer: Tracer) -> None:
        self.model_id = inner.model_id
        self._inner = inner
        self._tracer = tracer

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        with telemetry.embeddings_span(self._tracer, self.model_id):
            return self._inner.embed(texts)


def model_file_sha256(model_id: str, cache_dir: Path) -> str:
    """SHA-256 of the ONNX file fastembed loads for `model_id` from `cache_dir`.

    The embedding asset's manifest records it beside the model id: fastembed ships its own
    export, so a revision change moves the vectors under the same id (test design C-7).
    """
    from fastembed import TextEmbedding  # pyright: ignore[reportMissingTypeStubs]

    factory = cast(Any, TextEmbedding)
    supported = cast(list[dict[str, Any]], factory.list_supported_models())
    entry = next((m for m in supported if m.get("model") == model_id), None)
    if entry is None:
        raise ValueError(f"fastembed does not list the model {model_id!r}")
    file_name = Path(str(entry["model_file"])).name
    hf_repo = str(cast(dict[str, Any], entry.get("sources") or {}).get("hf") or "")
    repo_dir = f"models--{hf_repo.replace('/', '--')}" if hf_repo else ""
    # Several models share a file name; only a path under this model's own repo directory counts.
    found = sorted(
        p
        for p in cache_dir.rglob(file_name)
        if p.is_file() and (not repo_dir or repo_dir in p.parts)
    )
    if not found:
        raise FileNotFoundError(f"no {file_name} for {model_id} under {cache_dir}")
    digest = hashlib.sha256()
    with found[0].open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()
