# The one app image (AD-2). The process is chosen by command:
#   ticketscope-api | ticketscope-migrate | ticketscope-load
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

FROM ${PYTHON_IMAGE}
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=build /app /app
COPY migrations /app/migrations
USER 10001:10001
EXPOSE 8080
CMD ["ticketscope-api"]
