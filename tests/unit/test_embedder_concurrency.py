"""Inference workspace is exclusive for each adapter, through lazy materialization."""

import sys
import types
from collections.abc import Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event, Lock

import pytest

from ticketscope.adapters import embedder as module


def test_concurrent_calls_serialize_lazy_inference(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workers = 16
    attempted = 0
    guard = Lock()
    all_attempted = Event()
    inference_lock = Lock()
    active = 0
    peaks: list[int] = []

    class ObservedLock:
        def __enter__(self) -> None:
            nonlocal attempted
            with guard:
                attempted += 1
                if attempted == workers:
                    all_attempted.set()
            inference_lock.acquire()

        def __exit__(self, *args: object) -> None:
            inference_lock.release()

    class Vector:
        def __init__(self, value: float) -> None:
            self.value = value

        def tolist(self) -> list[float]:
            assert active == 1  # conversion is still inside exclusive inference
            return [self.value]

    class Model:
        def __init__(self, **kwargs: object) -> None:
            pass

        def embed(self, texts: Iterable[str]) -> Iterator[Vector]:
            nonlocal active
            # The generator body runs only when consumed, not when embed() returns.
            with guard:
                active += 1
                peaks.append(active)
            try:
                assert all_attempted.wait(5), "concurrent callers never reached the lock"
                for text in texts:
                    yield Vector(float(text))
            finally:
                with guard:
                    active -= 1

    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=Model))
    monkeypatch.setattr(module, "Lock", ObservedLock)
    adapter = module.FastEmbedEmbedder("fake", tmp_path)
    start = Barrier(workers)

    def call(number: int) -> list[list[float]]:
        start.wait(timeout=5)
        return adapter.embed([str(number), str(number + 100)])

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(call, range(workers)))
    assert results == [[[float(n)], [float(n + 100)]] for n in range(workers)]
    assert peaks == [1] * workers
    assert active == 0


@pytest.mark.parametrize("failure", ["embed", "iteration", "tolist"])
def test_inference_lock_released_after_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: str
) -> None:
    inference_lock = Lock()
    fail = True

    class Vector:
        def tolist(self) -> list[float]:
            if fail and failure == "tolist":
                raise RuntimeError("failed")
            return [1.0]

    class Model:
        def __init__(self, **kwargs: object) -> None:
            pass

        def embed(self, texts: Iterable[str]) -> Iterator[Vector]:
            if fail and failure == "embed":
                raise RuntimeError("failed")

            def vectors() -> Iterator[Vector]:
                if fail and failure == "iteration":
                    raise RuntimeError("failed")
                yield Vector()

            return vectors()

    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=Model))
    monkeypatch.setattr(module, "Lock", lambda: inference_lock)
    adapter = module.FastEmbedEmbedder("fake", tmp_path)
    with pytest.raises(RuntimeError, match="failed"):
        adapter.embed(["text"])
    assert inference_lock.acquire(blocking=False), "exception left the inference lock held"
    inference_lock.release()
    fail = False
    assert adapter.embed(["text"]) == [[1.0]]
