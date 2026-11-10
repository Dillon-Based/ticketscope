"""The built app image embeds with the network disabled (story 3.1 AC-6; epic 3 retro, G1).

AC-6: "Given the built app image, when it embeds a text with the network disabled, then it
succeeds." The model is baked into /models and the runtime is offline (HF_HUB_OFFLINE=1); this
runs the image under `docker run --network none` and embeds through the app's own adapter.

Skipped unless `TICKETSCOPE_TEST_APP_IMAGE` names a built `images/app.Dockerfile` image and
docker is available. ci.yml's `containers` job sets it, and sets
`TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1` so a missing image fails instead of skipping.
"""

import os
import shutil
import subprocess

import pytest

from tests.target import embeddings_pin

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
