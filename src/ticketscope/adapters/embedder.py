"""The `Embedder` adapters: fastembed over the baked ONNX model, and a traced wrapper.

The model is read from a local cache only (it is baked into the image, and the runtime is
offline). `core` never imports this: the `embeddings {model}` span is emitted here (AD-1,
AD-10).
"""

from collections.abc import Iterable, Sequence
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


class FastEmbedEmbedder:
    """`Embedder` over fastembed's `TextEmbedding`. Loading the model is eager."""

    def __init__(self, model_id: str, cache_dir: Path) -> None:
        # Imported here: jobs and tests that never embed do not load onnxruntime.
        from fastembed import TextEmbedding  # pyright: ignore[reportMissingTypeStubs]

        self.model_id = model_id
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
