"""The built app image embeds with the network disabled (story 3.1 AC-6; epic 3 retro, G1).

AC-6: "Given the built app image, when it embeds a text with the network disabled, then it
succeeds." The model is baked into /models and the runtime is offline (HF_HUB_OFFLINE=1); this
runs the image under `docker run --network none` and embeds through the app's own adapter.

Skipped unless `TICKETSCOPE_TEST_APP_IMAGE` names a built `images/app.Dockerfile` image and
docker is available. ci.yml's `containers` job sets it, and sets
`TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1` so a missing image fails instead of skipping.
"""

import json
import math
import os
import re
import shutil
import subprocess
from typing import Any

import pytest

from tests.target import REPO, embeddings_pin

IMAGE = os.environ.get("TICKETSCOPE_TEST_APP_IMAGE", "")
REQUIRED = os.environ.get("TICKETSCOPE_REQUIRE_CONTAINER_TESTS") == "1"

# Built from the settings the chart sets at runtime (TICKETSCOPE_EMBEDDING_MODEL_ID; the cache
# dir comes from the image's own env), as api builds its embedder.
EMBED = (
    "from ticketscope.adapters.embedder import FastEmbedEmbedder\n"
    "from ticketscope.settings import Settings\n"
    "s = Settings()\n"
    "e = FastEmbedEmbedder(s.embedding_model_id, s.embedding_cache_dir)\n"
    "[v] = e.embed(['launcher crash when opening a world'])\n"
    "print(e.model_id, len(v), round(sum(x * x for x in v), 3))\n"
)


@pytest.fixture(scope="module")
def image() -> str:
    if not IMAGE or shutil.which("docker") is None:
        if REQUIRED:
            pytest.fail("TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1 but no app image or docker")
        pytest.skip("needs docker and TICKETSCOPE_TEST_APP_IMAGE")
    return IMAGE


@pytest.mark.criterion("ticketscope--e3-s1--AC-6")
def test_the_app_image_embeds_with_the_network_disabled(image: str) -> None:
    model_id = embeddings_pin()["modelId"]
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "-e",
            f"TICKETSCOPE_EMBEDDING_MODEL_ID={model_id}",
            image,
            "python",
            "-c",
            EMBED,
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    model, dim, norm = result.stdout.split()[-3:]
    assert model == model_id
    assert dim == "384"
    assert norm == "1.0"  # fastembed L2-normalises: a real vector, not zeros


# --- the embedder against committed reference vectors (story 5.13, DW-3, R-004) -----------------
# The reference was made with onnxruntime and tokenizers alone (scripts/reference_vectors.py). Each
# CI `images` leg runs this on its own architecture, so arm64 is checked, not assumed.

REFERENCE = REPO / "tests" / "fixtures" / "embedder_reference.json"

EMBED_REFERENCE = (
    "import json, sys\n"
    "from ticketscope.adapters.embedder import FastEmbedEmbedder, model_file_sha256\n"
    "from ticketscope.settings import Settings\n"
    "s = Settings()\n"
    "e = FastEmbedEmbedder(s.embedding_model_id, s.embedding_cache_dir)\n"
    "texts = json.load(sys.stdin)\n"
    "# One text per call, as the reference was made: batch padding moves a short text's vector\n"
    "# by up to ~1e-3 beside a long one, which is not what this test is about.\n"
    "print(json.dumps({'vectors': [e.embed([t])[0] for t in texts],\n"
    "  'sha256': model_file_sha256(s.embedding_model_id, s.embedding_cache_dir)}))\n"
)


def _embed_reference_texts(image: str, texts: list[str]) -> dict[str, Any]:
    model_id = embeddings_pin()["modelId"]
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            "none",
            "-e",
            f"TICKETSCOPE_EMBEDDING_MODEL_ID={model_id}",
            image,
            "python",
            "-c",
            EMBED_REFERENCE,
        ],
        input=json.dumps(texts),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout.splitlines()[-1])


@pytest.mark.criterion("ticketscope--e5-s13--AC-3")
def test_the_image_embedder_matches_the_reference_vectors(image: str) -> None:
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    min_cosine = ref["tolerance"]["min_cosine"]
    max_diff = ref["tolerance"]["max_component_diff"]
    got = _embed_reference_texts(image, ref["texts"])["vectors"]
    assert len(got) == len(ref["texts"])
    for text, want, have in zip(ref["texts"], ref["vectors"], got, strict=True):
        dot = sum(a * b for a, b in zip(want, have, strict=True))
        norm = math.sqrt(sum(a * a for a in want)) * math.sqrt(sum(b * b for b in have))
        diff = max(abs(a - b) for a, b in zip(want, have, strict=True))
        assert dot / norm >= min_cosine and diff <= max_diff, (
            f"{text[:60]!r}: cosine {dot / norm:.6f} (min {min_cosine}), "
            f"largest component difference {diff:.6f} (max {max_diff})"
        )


@pytest.mark.criterion("ticketscope--e5-s13--AC-2")
def test_the_image_model_file_is_the_pinned_one(image: str) -> None:
    dockerfile = (REPO / "images" / "app.Dockerfile").read_text(encoding="utf-8")
    match = re.search(r"^ARG EMBEDDING_MODEL_SHA256=(\w+)$", dockerfile, re.MULTILINE)
    assert match
    assert _embed_reference_texts(image, ["pin"])["sha256"] == match.group(1)
