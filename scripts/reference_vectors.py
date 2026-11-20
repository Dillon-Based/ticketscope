"""Oracle generator for the embedder's reference vectors (DW-3, risk R-004).

Run by a person, never by CI; it prints the JSON committed as
`tests/fixtures/embedder_reference.json`. It embeds with `onnxruntime` and `tokenizers`
directly and never imports fastembed or any ticketscope code, so the reference is independent
of the code under test.

    uv run python scripts/reference_vectors.py > tests/fixtures/embedder_reference.json

It downloads Qdrant/bge-small-en-v1.5-onnx-Q at the revision pinned in `images/app.Dockerfile`
and refuses a file whose SHA-256 differs from that pin. Preprocessing is BGE's: truncate to 512
tokens, take the CLS token of the last hidden state, L2-normalise.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent.parent
REPO_ID = "Qdrant/bge-small-en-v1.5-onnx-Q"
MAX_TOKENS = 512
TOLERANCE = {"min_cosine": 0.9999, "max_component_diff": 2e-3}

TEXTS = [
    "Launcher crashes when opening a world after updating to 1.21",
    "Creeper explosion does not damage item frames on walls",
    "Villagers stop trading after being cured of zombification",
    "Elytra durability is not reduced when flying through a nether portal",
    "Redstone comparator reads wrong signal strength from a composter",
    "Game freezes on startup with shaders enabled on Apple silicon",
    "Cannot join realm: Unable to connect to world",
    "crash",
    " ".join(
        f"Step {i}: place the hopper under the chest, then break the chest while the "
        "minecart is moving and the world saves its chunks."
        for i in range(1, 60)
    ),
]


def _pin(name: str) -> str:
    text = (ROOT / "images" / "app.Dockerfile").read_text(encoding="utf-8")
    match = re.search(rf"^ARG {name}=(\S+)$", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"app.Dockerfile has no {name}")
    return match.group(1)


def main() -> None:
    revision = _pin("EMBEDDING_MODEL_REVISION")
    expected = _pin("EMBEDDING_MODEL_SHA256")
    snapshot = Path(snapshot_download(repo_id=REPO_ID, revision=revision))
    onnx_path = snapshot / "model_optimized.onnx"
    actual = hashlib.sha256(onnx_path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"sha256 mismatch: expected {expected}, actual {actual}")

    tokenizer = Tokenizer.from_file(str(snapshot / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=MAX_TOKENS)
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    wanted = {i.name for i in session.get_inputs()}

    vectors: list[list[float]] = []
    for text in TEXTS:
        enc = tokenizer.encode(text)
        feeds = {
            "input_ids": np.array([enc.ids], dtype=np.int64),
            "attention_mask": np.array([enc.attention_mask], dtype=np.int64),
            "token_type_ids": np.array([enc.type_ids], dtype=np.int64),
        }
        hidden = session.run(None, {k: v for k, v in feeds.items() if k in wanted})[0]
        cls = hidden[0, 0, :].astype(np.float64)
        vectors.append((cls / np.linalg.norm(cls)).tolist())

    json.dump(
        {
            "model_repo": REPO_ID,
            "revision": revision,
            "model_sha256": actual,
            "tolerance": TOLERANCE,
            "texts": TEXTS,
            "vectors": vectors,
        },
        sys.stdout,
        indent=1,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
