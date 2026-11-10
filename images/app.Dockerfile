# The one app image (AD-2). The process is chosen by command:
#   ticketscope-api | ticketscope-migrate | ticketscope-load | ticketscope-eval
# ingest runs on a person's machine (scripts/publish-snapshot.sh); its `ingest`
# dependency group (pymongo) is not installed here.
# Build from the repo root: docker build -f images/app.Dockerfile .
ARG PYTHON_IMAGE=python:3.14-slim-trixie

FROM ghcr.io/astral-sh/uv:0.13 AS uv

FROM ${PYTHON_IMAGE} AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
# No snapshot ships in the image: load fetches the pinned Release asset (AD-6).

# The embedding model is read from Hugging Face only here, in a build stage (AD-21). It must
# equal the chart's embeddings.modelId (a unit test pins it).
FROM build AS model
ARG EMBEDDING_MODEL_ID=BAAI/bge-small-en-v1.5
ENV EMBEDDING_MODEL_ID=${EMBEDDING_MODEL_ID}
RUN /app/.venv/bin/python -c "import os; from fastembed import TextEmbedding; \
TextEmbedding(model_name=os.environ['EMBEDDING_MODEL_ID'], cache_dir='/models')" \
 && chmod -R a+rX /models

FROM ${PYTHON_IMAGE}
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1 \
    ORT_DISABLE_TELEMETRY=1 \
    FASTEMBED_CACHE_PATH=/models \
    TICKETSCOPE_EMBEDDING_CACHE_DIR=/models
WORKDIR /app
COPY --from=build /app /app
# The runtime is offline: the model is read from /models and nothing else.
COPY --from=model /models /models
COPY migrations /app/migrations
# eval reads eval/pairs/<snapshot_version>.jsonl relative to /app (AD-26).
COPY eval/pairs /app/eval/pairs
USER 10001:10001
EXPOSE 8080
CMD ["ticketscope-api"]
