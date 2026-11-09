"""The chart's embeddings wiring (story 3.1, AD-21): model env only with `computeOnKind`,
and one model id shared by the app image build and `values.yaml`."""

import re
import shutil
import subprocess

import pytest

from tests.target import CHART_VALUES, REPO

CHART = REPO / "deploy" / "charts" / "ticketscope"
_ARGS = [
    "--set-string",
    "image.app.tag=t",
    "--set-string",
    "image.postgres.tag=18-t",
    "--set",
    "backup.enabled=false",
]
MODEL_ENV = "TICKETSCOPE_EMBEDDING_MODEL_ID"
COMPUTE_ENV = "TICKETSCOPE_EMBEDDINGS_COMPUTE"

needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")


def _render(*args: str) -> str:
    result = subprocess.run(
        ["helm", "template", "t", str(CHART), *_ARGS, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _doc(rendered: str, name: str) -> str:
    kind = "Deployment" if name == "ticketscope-api" else "Job"
    [doc] = [
        d for d in rendered.split("\n---\n") if f"kind: {kind}\n" in d and f"name: {name}\n" in d
    ]
    return doc


def _values_model() -> str:
    text = CHART_VALUES.read_text(encoding="utf-8")
    match = re.search(r'^embeddings:\n(?:[ #].*\n)*?  modelId: "([^"]+)"', text, re.MULTILINE)
    assert match, "embeddings.modelId not found in values.yaml"
    return match.group(1)


@needs_helm
def test_flag_off_renders_no_model_env_on_api_or_load() -> None:
    rendered = _render()
    for name in ("ticketscope-api", "ticketscope-load"):
        doc = _doc(rendered, name)
        assert MODEL_ENV not in doc
        assert COMPUTE_ENV not in doc
    assert "memory: 384Mi" in _doc(rendered, "ticketscope-api")
    assert "memory: 512Mi" in _doc(rendered, "ticketscope-load")  # the Job limit stays


@needs_helm
def test_flag_on_sets_the_model_on_api_and_load_and_compute_on_load_only() -> None:
    rendered = _render("--set", "embeddings.computeOnKind=true")
    model = _values_model()
    api, load = _doc(rendered, "ticketscope-api"), _doc(rendered, "ticketscope-load")
    for doc in (api, load):
        assert f'- name: {MODEL_ENV}\n              value: "{model}"' in doc
    assert f'- name: {COMPUTE_ENV}\n              value: "true"' in load
    assert COMPUTE_ENV not in api
    assert "memory: 2Gi" in load  # the load Job limit is raised only here
    assert "activeDeadlineSeconds: 3000" in load


@needs_helm
def test_the_eval_job_never_gets_the_model() -> None:
    rendered = _render("--set", "embeddings.computeOnKind=true", "--set", "eval.enabled=true")
    assert MODEL_ENV not in _doc(rendered, "ticketscope-eval")


def test_the_dockerfile_and_values_name_the_same_model() -> None:
    dockerfile = (REPO / "images" / "app.Dockerfile").read_text(encoding="utf-8")
    match = re.search(r"^ARG EMBEDDING_MODEL_ID=(\S+)$", dockerfile, re.MULTILINE)
    assert match, "app.Dockerfile has no EMBEDDING_MODEL_ID build argument"
    assert match.group(1) == _values_model()


def test_the_image_reads_hugging_face_only_in_a_build_stage_and_runs_offline() -> None:
    dockerfile = (REPO / "images" / "app.Dockerfile").read_text(encoding="utf-8")
    stages = dockerfile.split("\nFROM ")
    download = [s for s in stages if "TextEmbedding(" in s]
    assert len(download) == 1 and download[0].startswith("build AS model")
    runtime = stages[-1]
    assert "HF_HUB_OFFLINE=1" in runtime
    assert "COPY --from=model /models /models" in runtime
