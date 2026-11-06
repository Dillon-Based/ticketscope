"""The api process: app factory and its single composition root (AD-1).

This is the only `http` module allowed to import a driven adapter.
"""

import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Response

from ticketscope.contract.search import (
    Issue,
    Outcome,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from ticketscope.core.modes import REGISTRY
from ticketscope.core.ports import CorpusStore
from ticketscope.settings import Settings

log = logging.getLogger(__name__)


def create_app(store: CorpusStore | None = None, settings: Settings | None = None) -> FastAPI:
    """Build the app. Without a `store`, wire the Postgres adapter as `ticketscope_ro`."""
    settings = settings or Settings()
    if store is None:
        from ticketscope.adapters.postgres import PostgresCorpusStore

        store = PostgresCorpusStore(settings.conninfo())
    corpus = store
    default_mode = settings.default_mode

    app = FastAPI(title="ticketscope", version="1")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz(response: Response) -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        try:
            version = corpus.corpus_version()
        except Exception as exc:
            log.warning("readiness check failed: %s", exc)
            version = None
        if version is None:
            response.status_code = 503
            return {"status": "corpus not loaded"}
        return {"status": "ready", "corpus_version": version}

    @app.post("/v1/search")
    def search(request: SearchRequest) -> SearchResponse:  # pyright: ignore[reportUnusedFunction]
        mode_name = request.mode or default_mode
        mode = REGISTRY.get(mode_name)
        if mode is None:
            raise HTTPException(status_code=422, detail=f"unknown mode: {mode_name}")
        version = corpus.corpus_version()
        if version is None:
            raise HTTPException(status_code=503, detail="corpus not loaded")
        hits = mode.build(corpus).search(request.query, request.k)
        return SearchResponse(
            mode=mode.name,  # pyright: ignore[reportArgumentType]
            score_kind=mode.score_kind,
            corpus_version=version,
            results=[
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
                    outcome=Outcome(
                        status=hit.issue.outcome_status,
                        summary=hit.issue.outcome_summary,
                        source=hit.issue.outcome_source,
                        ref=hit.issue.outcome_ref,
                    ),
                )
                for rank, hit in enumerate(hits, start=1)
            ],
        )

    return app


def main() -> None:
    settings = Settings()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "ticketscope.http.app:create_app",
        factory=True,
        host=settings.http_host,
        port=settings.http_port,
    )
