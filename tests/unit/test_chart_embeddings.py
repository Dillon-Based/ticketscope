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


# The merged pin in values.yaml is real, so the tests about "no pin" clear it explicitly.
_NO_PIN = ["--set-string", "embeddings.assetVersion=", "--set-string", "embeddings.sha256="]


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
    rendered = _render(*_NO_PIN)
    for name in ("ticketscope-api", "ticketscope-load"):
        doc = _doc(rendered, name)
        assert MODEL_ENV not in doc
        assert COMPUTE_ENV not in doc
    assert "memory: 512Mi" in _doc(rendered, "ticketscope-api")
    assert "memory: 512Mi" in _doc(rendered, "ticketscope-load")  # the Job limit stays


@needs_helm
def test_flag_on_sets_the_model_on_api_and_load_and_compute_on_load_only() -> None:
    rendered = _render(*_NO_PIN, "--set", "embeddings.computeOnKind=true")
    model = _values_model()
    api, load = _doc(rendered, "ticketscope-api"), _doc(rendered, "ticketscope-load")
    for doc in (api, load):
        assert f'- name: {MODEL_ENV}\n              value: "{model}"' in doc
    assert f'- name: {COMPUTE_ENV}\n              value: "true"' in load
    assert COMPUTE_ENV not in api
    assert "memory: 2Gi" in load  # the load Job limit is raised only here
    assert "activeDeadlineSeconds: 3000" in load


@needs_helm
def test_the_eval_job_gets_the_model_so_it_can_embed_queries_live() -> None:
    model = _values_model()
    for flags in (("--set", "embeddings.computeOnKind=true"), ()):
        rendered = _render(*flags, "--set", "eval.enabled=true")
        doc = _doc(rendered, "ticketscope-eval")
        assert f'- name: {MODEL_ENV}\n              value: "{model}"' in doc
        assert COMPUTE_ENV not in doc  # eval never computes the corpus's embeddings
        assert "memory: 1Gi" in doc  # model plus scoring; jobs.resources is too small


@needs_helm
def test_the_eval_job_has_no_model_when_embeddings_are_off() -> None:
    rendered = _render(*_NO_PIN, "--set", "eval.enabled=true")
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
    # onnxruntime's telemetry warning goes to stdout as a non-JSON line and breaks the api's
    # JSON-lines logs; the runtime image has no writable home to persist its device id in.
    assert "ORT_DISABLE_TELEMETRY=1" in runtime


# --- the pinned embedding asset (story 4, AD-25) -----------------------------------------------

ASSET_ENV = "TICKETSCOPE_EMBEDDINGS_ASSET_VERSION"
SHA_ENV = "TICKETSCOPE_EMBEDDINGS_SHA256"
_SHA = "ab" * 32
_PIN = [
    "--set-string",
    "embeddings.assetVersion=2026.11.1",
    "--set-string",
    f"embeddings.sha256={_SHA}",
]


@needs_helm
def test_no_pin_renders_no_asset_env() -> None:
    load = _doc(_render(*_NO_PIN), "ticketscope-load")
    assert ASSET_ENV not in load and SHA_ENV not in load


@needs_helm
def test_a_pin_gives_load_the_asset_and_the_model_and_api_the_model() -> None:
    rendered = _render(*_PIN)
    model = _values_model()
    api, load = _doc(rendered, "ticketscope-api"), _doc(rendered, "ticketscope-load")
    for doc in (api, load):
        assert f'- name: {MODEL_ENV}\n              value: "{model}"' in doc
    assert f'- name: {ASSET_ENV}\n              value: "2026.11.1"' in load
    assert f'- name: {SHA_ENV}\n              value: "{_SHA}"' in load
    assert ASSET_ENV not in api and SHA_ENV not in api
    assert COMPUTE_ENV not in load  # nothing is computed
    # The asset load needs the ordinary Job limit and deadline, not the compute ones.
    assert "memory: 512Mi" in load and "activeDeadlineSeconds: 900" in load


@needs_helm
def test_a_pinned_asset_wins_over_compute_on_kind() -> None:
    load = _doc(_render(*_PIN, "--set", "embeddings.computeOnKind=true"), "ticketscope-load")
    assert COMPUTE_ENV not in load
    assert ASSET_ENV in load
    assert "memory: 2Gi" not in load and "activeDeadlineSeconds: 3000" not in load


@needs_helm
def test_a_pinned_version_with_an_empty_checksum_fails_to_render() -> None:
    result = subprocess.run(
        [
            "helm",
            "template",
            "t",
            str(CHART),
            *_ARGS,
            "--set-string",
            "embeddings.assetVersion=2026.11.1",
            "--set-string",
            "embeddings.sha256=",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "embeddings.sha256 is required" in result.stderr


@needs_helm
def test_the_eval_job_never_gets_the_asset_pin() -> None:
    rendered = _render(*_PIN, "--set", "eval.enabled=true")
    eval_job = _doc(rendered, "ticketscope-eval")
    assert ASSET_ENV not in eval_job and SHA_ENV not in eval_job
