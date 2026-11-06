# The one app image (AD-2). The process is chosen by command:
#   ticketscope-api | ticketscope-migrate | ticketscope-load
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
# The fixture snapshot ships in the image under version `fixture` (pinned in values).
COPY snapshot/fixture.jsonl snapshot/fixture-kinds.json /tmp/snapshot/
RUN mkdir -p /app/snapshots \
 && gzip -9 -n -c /tmp/snapshot/fixture.jsonl > /app/snapshots/fixture.jsonl.gz \
 && cp /tmp/snapshot/fixture-kinds.json /app/snapshots/fixture-kinds.json

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
