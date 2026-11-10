"""The api process: app factory and its single composition root (AD-1).

This is the only `http` module allowed to import a driven adapter.
"""

import logging
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from opentelemetry.sdk.trace import TracerProvider
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from ticketscope import telemetry
from ticketscope.adapters.embedder import FastEmbedEmbedder, TracedEmbedder
from ticketscope.contract.search import (
    Issue,
    IssueDetail,
    IssueResponse,
    Outcome,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.modes import REGISTRY
from ticketscope.core.ports import CorpusStore, Embedder
from ticketscope.http import page
from ticketscope.settings import Settings

log = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


def _problem(
    status: int,
    detail: str,
    headers: Mapping[str, str] | None = None,
    **extra: object,
) -> JSONResponse:
    """An RFC 9457 problem body: every `/v1` error (AD-4, Errors convention)."""
    body = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        **extra,
    }
    return JSONResponse(
        body,
        status_code=status,
        headers=dict(headers) if headers else None,
        media_type=PROBLEM_JSON,
    )


def _field(loc: Sequence[Any]) -> str:
    """A validation `loc` without its source (`body`, `path`, `query`): `k`, `number`."""
    parts = list(loc[1:]) if loc and loc[0] in ("body", "path", "query", "header") else list(loc)
    return ".".join(str(p) for p in parts)


async def _http_problem(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    headers = exc.headers
    if exc.status_code == 405 and request.url.path == "/":
        # Separate GET/POST routes otherwise report only the first partial match.
        headers = {**(headers or {}), "Allow": "GET, POST"}
    return _problem(exc.status_code, exc.detail, headers=headers)


async def _validation_problem(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors: list[dict[str, Any]] = []
    lines: list[str] = []
    for error in exc.errors():
        loc: list[Any] = list(error.get("loc", ()))
        msg = str(error.get("msg", ""))
        errors.append({"loc": loc, "msg": msg})
        # A malformed body's loc is ("body", <char offset>): name the body, not the offset.
        field = "body" if error.get("type") == "json_invalid" else _field(loc)
        lines.append(f"{field}: {msg}" if field else msg)
    return _problem(422, "; ".join(lines) or "request validation failed", errors=errors)


async def _server_problem(_request: Request, _exc: Exception) -> JSONResponse:
    # Starlette re-raises after this response, so the server still logs the traceback.
    return _problem(500, "internal server error")


def _outcome(issue: IssueRecord) -> Outcome:
    return Outcome(
        status=issue.outcome_status,
        summary=issue.outcome_summary,
        source=issue.outcome_source,
        ref=issue.outcome_ref,
    )


def _results(hits: list[Scored]) -> list[SearchResult]:
    """Ranked hits as `/v1` results: the one result shape for the API and the page (AD-4)."""
    return [
        SearchResult(
            rank=rank,
            score=hit.score,
            issue=Issue(
                number=hit.issue.number,
                title=hit.issue.title,
                url=hit.issue.url,
                kind=hit.issue.kind,
                state=hit.issue.state,
            ),
            outcome=_outcome(hit.issue),
        )
        for rank, hit in enumerate(hits, start=1)
    ]


PAGE_MODE = "keyword"
PAGE_K = 10


def create_app(
    store: CorpusStore | None = None,
    settings: Settings | None = None,
    tracer_provider: TracerProvider | None = None,
    embedder: Embedder | None = None,
) -> FastAPI:
    """Build the app. Without a `store`, wire the Postgres adapter as `ticketscope_ro`.
    Without a `tracer_provider`, spans go to the global one (`telemetry.setup` in `main`).
    Without an `embedder` but with `settings.embedding_model_id`, load the baked model now,
    so a missing model fails startup rather than the first dense search."""
    settings = settings or Settings()
    if store is None:
        from ticketscope.adapters.postgres import PostgresCorpusStore

        store = PostgresCorpusStore(settings.conninfo())
    corpus = store
    default_mode = settings.default_mode
    record_query_text = settings.trace_query_text
    tracer = telemetry.get_tracer(tracer_provider)
    model_id = settings.embedding_model_id
    if embedder is None and model_id:
        embedder = FastEmbedEmbedder(
            model_id, settings.embedding_cache_dir, threads=settings.embedding_threads or None
        )
    # The `embeddings {model}` span comes from the adapter side, whoever the embedder is.
    query_embedder = TracedEmbedder(embedder, tracer) if embedder is not None else None

    app = FastAPI(title="ticketscope", version="1")
    app.add_exception_handler(StarletteHTTPException, _http_problem)
    app.add_exception_handler(RequestValidationError, _validation_problem)
    app.add_exception_handler(Exception, _server_problem)
    telemetry.instrument_app(app, tracer_provider, record_query_text)

    def retrieve(mode_name: str, query: str, k: int, version: str) -> list[Scored]:
        """One registry mode's search inside the AD-10 retrieval span."""
        with telemetry.retrieval_span(
            tracer,
            mode=mode_name,
            k=k,
            corpus_version=version,
            query=query,
            record_query_text=record_query_text,
        ) as span:
            hits = REGISTRY[mode_name].build(corpus, query_embedder).search(query, k)
            span.result_count(len(hits))
        return hits

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz(response: Response) -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        try:
            # Probes are not traced (AD-10): neither the SERVER span nor its db query.
            with telemetry.untraced():
                version = corpus.corpus_version()
        except Exception as exc:
            log.warning("readiness check failed: %s", exc)
            version = None
        if version is None:
            response.status_code = 503
            return {"status": "corpus not loaded"}
        if model_id:
            # The api embeds queries with `model_id`: it must be the model `load` used.
            try:
                with telemetry.untraced():
                    stored = corpus.embedding_model_id()
            except Exception as exc:
                log.warning("readiness check failed: %s", exc)
                stored = None
            if stored != model_id:
                response.status_code = 503
                return {
                    "status": "embedding model mismatch",
                    "reason": f"api model is {model_id!r}, corpus_meta embedding model is "
                    f"{stored!r}",
                }
        return {"status": "ready", "corpus_version": version}

    @app.post("/v1/search")
    def search(request: SearchRequest) -> SearchResponse:  # pyright: ignore[reportUnusedFunction]
        mode_name = request.mode or default_mode
        mode = REGISTRY.get(mode_name)
        if mode is None:
            # Same shape as a Literal miss: AD-4 validates `mode` against the registry.
            raise RequestValidationError(
                [
                    {
                        "type": "value_error",
                        "loc": ("body", "mode"),
                        "msg": f"unknown mode: {mode_name}",
                        "input": mode_name,
                    }
                ]
            )
        version = corpus.corpus_version()
        if version is None:
            raise HTTPException(status_code=503, detail="corpus not loaded")
        if not mode.available(corpus, query_embedder):
            raise HTTPException(status_code=503, detail=f"mode {mode.name} is not available")
        hits = retrieve(mode.name, request.query, request.k, version)
        return SearchResponse(
            mode=mode.name,  # pyright: ignore[reportArgumentType]
            score_kind=mode.score_kind,
            corpus_version=version,
            results=_results(hits),
        )

    def render_page(query: str) -> HTMLResponse:
        # The page answers its own errors in HTML; the global handler's problem+json
        # is for /v1, not a browser.
        if not query.strip():
            return HTMLResponse(page.render(query, message=page.BLANK_MESSAGE))
        try:
            version = corpus.corpus_version()
            if version is None:
                return HTMLResponse(
                    page.render(query, message=page.NOT_LOADED_MESSAGE, error=True),
                    status_code=503,
                )
            hits = retrieve(PAGE_MODE, query, PAGE_K, version)
            if not hits:
                return HTMLResponse(page.render(query, message=page.NO_MATCH_MESSAGE))
            return HTMLResponse(page.render(query, _results(hits)))
        except Exception:
            log.exception("search page failed")
            return HTMLResponse(
                page.render(query, message=page.ERROR_MESSAGE, error=True), status_code=500
            )

    @app.get("/", response_class=HTMLResponse)
    def page_get(q: str = "") -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        return render_page(q)

    @app.post("/", response_class=HTMLResponse)
    async def page_post(request: Request) -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        # Form-encoded by hand: FastAPI's Form needs python-multipart for one field.
        form = parse_qs((await request.body()).decode("utf-8", errors="replace"))
        # The store call blocks: keep it off the event loop, as FastAPI does for sync routes.
        return await run_in_threadpool(render_page, form.get("q", [""])[-1])

    @app.get("/v1/issues/{number}")
    def get_issue(number: int) -> IssueResponse:  # pyright: ignore[reportUnusedFunction]
        if corpus.corpus_version() is None:
            raise HTTPException(status_code=503, detail="corpus not loaded")
        found = corpus.get_issue(number)
        if found is None:
            raise HTTPException(status_code=404, detail=f"issue {number} not found")
        issue = found.issue
        return IssueResponse(
            issue=IssueDetail(
                number=issue.number,
                title=issue.title,
                url=issue.url,
                kind=issue.kind,
                state=issue.state,
                body=found.body,
            ),
            outcome=_outcome(issue),
        )

    return app


def main() -> None:
    settings = Settings()
    # JSON logs and the global provider before uvicorn starts; `log_config=None` keeps
    # uvicorn's own loggers on the JSON root handler.
    telemetry.setup(telemetry.SERVICE_API, settings.otlp_endpoint)
    uvicorn.run(
        "ticketscope.http.app:create_app",
        factory=True,
        host=settings.http_host,
        port=settings.http_port,
        log_config=None,
    )
