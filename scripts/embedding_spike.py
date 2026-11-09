"""Spike 3.3 harness: score one embedding model on the loaded kind corpus.

Throwaway measurement tooling, not product code. It embeds every loaded issue with one model,
stores the vectors in `issue_embedding` under a model key, scores keyword, dense and hybrid with
core's own retrievers and the eval's tallies on the committed pairs file, then removes the rows.
Run one process per model so the peak-memory figures are not shared between models.

    kubectl -n ticketscope port-forward svc/ticketscope-db-rw 15432:5432 &
    SPIKE_DB_PASSWORD=... SPIKE_DB_USER=... uv run python scripts/embedding_spike.py \
        --model BAAI/bge-small-en-v1.5 --out /path/results

Environment: SPIKE_DB_HOST (127.0.0.1), SPIKE_DB_PORT (15432), SPIKE_DB_NAME (app),
SPIKE_DB_USER, SPIKE_DB_PASSWORD.
"""

import argparse
import json
import os
import resource
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import psycopg

from ticketscope.adapters.embedder import FastEmbedEmbedder
from ticketscope.adapters.postgres import PostgresCorpusStore, read_corpus_meta, vector_literal
from ticketscope.core.derive import EMBEDDING_MAX_CHARS, EMBEDDING_RULE_VERSION, embedding_text
from ticketscope.core.model import Scored
from ticketscope.core.modes import DenseRetriever, HybridRetriever, KeywordRetriever
from ticketscope.core.pairs import read_pairs
from ticketscope.core.ports import Retriever
from ticketscope.jobs.eval.score import K, _ModeTally, first_member_rank, query_text  # pyright: ignore[reportPrivateUsage]

BATCH = 8  # as `load` (EMBEDDING_BATCH_SIZE)
ROOT = Path(__file__).resolve().parent.parent


def rss_mb() -> float:
    """Peak resident set size of this process so far, in MB (macOS reports bytes)."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


class Keyed:
    """An `Embedder` that cuts text to `max_chars` and stores/searches under `model_id`."""

    def __init__(self, inner: FastEmbedEmbedder, key: str, max_chars: int) -> None:
        self.model_id = key
        self._inner = inner
        self._max = max_chars

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self._inner.embed([t[: self._max] for t in texts])


class Memo:
    """Caches one query's results so hybrid does not repeat dense's search."""

    def __init__(self, inner: Retriever) -> None:
        self._inner = inner
        self._key: tuple[str, int, frozenset[int]] | None = None
        self._value: list[Scored] = []

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        key = (query, k, exclude)
        if key != self._key:
            self._key, self._value = key, self._inner.search(query, k, exclude)
        return self._value


def truncated_share(model: Any, texts: list[str]) -> tuple[int, int, int]:
    """(issues over the model's token limit, issues counted, the limit), tokens counted without
    truncation. The limit is the tokenizer's own `max_length`."""
    from tokenizers import Tokenizer  # pyright: ignore[reportMissingTypeStubs]

    inner = model._model.model  # fastembed OnnxTextEmbedding
    limit = int(inner.tokenizer.truncation["max_length"])
    plain = Tokenizer.from_str(inner.tokenizer.to_str())
    plain.no_truncation()
    plain.no_padding()  # the model's tokenizer pads to the limit, which would count every issue
    over = sum(1 for e in plain.encode_batch(texts) if len(e.ids) > limit)
    return over, len(texts), limit


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--model", required=True, help="fastembed model id")
    ap.add_argument("--max-chars", type=int, default=EMBEDDING_MAX_CHARS, help="the cut (chars)")
    ap.add_argument("--max-pairs", type=int, default=0, help="score only the first N pairs")
    ap.add_argument("--limit-issues", type=int, default=0, help="embed only the first N issues")
    ap.add_argument("--cache-dir", type=Path, default=Path.home() / ".cache" / "spike-models")
    ap.add_argument("--out", type=Path, required=True, help="directory for the results JSON")
    ap.add_argument("--no-score", action="store_true", help="measure memory and cut only")
    ap.add_argument("--keep", action="store_true", help="leave the embedding rows in place")
    args = ap.parse_args()

    env = os.environ
    conninfo = (
        f"host={env.get('SPIKE_DB_HOST', '127.0.0.1')} port={env.get('SPIKE_DB_PORT', '15432')} "
        f"dbname={env.get('SPIKE_DB_NAME', 'app')} user={env['SPIKE_DB_USER']} "
        f"password={env['SPIKE_DB_PASSWORD']} connect_timeout=10"
    )
    meta = read_corpus_meta(conninfo)
    if meta is None:
        print(
            "no corpus loaded (corpus_meta is empty): run scripts/kind-up.sh first", file=sys.stderr
        )
        return 1
    pairs = read_pairs((ROOT / "eval" / "pairs" / f"{meta.snapshot_version}.jsonl").read_bytes())
    if args.max_pairs:
        pairs = pairs[: args.max_pairs]
    if args.no_score:
        pairs = []
    key = args.model if args.max_chars == EMBEDDING_MAX_CHARS else f"{args.model}@c{args.max_chars}"

    rss_start = rss_mb()
    t0 = time.perf_counter()
    try:
        inner = FastEmbedEmbedder(args.model, args.cache_dir)
    except Exception as exc:  # a model fastembed cannot load is a failed candidate
        print(f"candidate {args.model} failed to load: {exc}", file=sys.stderr)
        return 1
    inner.embed(["warm up"])
    load_seconds = time.perf_counter() - t0
    rss_loaded = rss_mb()
    embedder = Keyed(inner, key, args.max_chars)
    model_bytes = sum(
        p.stat().st_size
        for p in args.cache_dir.rglob("*")
        if p.is_file() and args.model.split("/")[-1].lower() in str(p).lower()
    )

    with psycopg.connect(conninfo) as conn:
        conn.execute("DELETE FROM issue_embedding WHERE model_id = %s", (key,))
        issues = conn.execute("SELECT number, title, body FROM issue ORDER BY number").fetchall()
    texts = [embedding_text(title, body)[: args.max_chars] for _, title, body in issues]
    over, counted, token_limit = truncated_share(inner, texts)  # always over every issue
    if args.limit_issues:
        issues, texts = issues[: args.limit_issues], texts[: args.limit_issues]

    embed_seconds = 0.0
    dimension = 0
    with (
        psycopg.connect(conninfo) as conn,
        conn.cursor().copy(
            "COPY issue_embedding (issue_number, model_id, embedding) FROM STDIN"
        ) as copy,
    ):
        for i in range(0, len(issues), BATCH):
            started = time.perf_counter()
            vectors = embedder.embed(texts[i : i + BATCH])
            dimension = len(vectors[0])
            embed_seconds += time.perf_counter() - started
            for (number, _, _), vec in zip(issues[i : i + BATCH], vectors, strict=True):
                copy.write_row((number, key, vector_literal(vec)))
    rss_embedded = rss_mb()

    store = PostgresCorpusStore(conninfo)
    keyword = KeywordRetriever(store)
    dense = Memo(DenseRetriever(store, embedder))
    retrievers: dict[str, Retriever] = {
        "keyword": keyword,
        "dense": dense,
        "hybrid": HybridRetriever(keyword, dense),
    }
    tallies = {name: _ModeTally() for name in retrievers}
    scored = 0
    for pair in pairs:
        text = query_text(store, pair.query)
        exclude = frozenset({pair.query})
        for name, retriever in retrievers.items():
            started = time.perf_counter()
            ranked = [h.issue.number for h in retriever.search(text, K, exclude=exclude)]
            tallies[name].add(
                pair,
                first_member_rank(pair.relevant, ranked),
                (time.perf_counter() - started) * 1000,
            )
        scored += 1
        if scored % 1000 == 0:
            print(f"  scored {scored}/{len(pairs)}", file=sys.stderr, flush=True)

    result = {
        "model": args.model,
        "key": key,
        "snapshot_version": meta.snapshot_version,
        "preprocessing_version": f"{meta.preprocessing_version or ''}".split(".emb")[0]
        + f".{EMBEDDING_RULE_VERSION}",
        "max_chars": args.max_chars,
        "token_limit": token_limit,
        "issues_embedded": len(issues),
        "issues_over_token_limit": over,
        "issues_counted": counted,
        "dimension": dimension,
        "model_load_seconds": round(load_seconds, 1),
        "embed_seconds_total": round(embed_seconds, 1),
        "embed_ms_per_issue": round(1000 * embed_seconds / max(len(issues), 1), 2),
        "rss_mb": {
            "before_model": round(rss_start),
            "after_model_load": round(rss_loaded),
            "peak_after_embedding": round(rss_embedded),
            "peak_end": round(rss_mb()),
        },
        "model_cache_bytes": model_bytes,
        "pairs_scored": scored,
        "modes": {
            n: {k: v for k, v in t.results().items() if k != "first_member_ranks"}
            for n, t in tallies.items()
        },
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{key.replace('/', '__').replace('@', '_')}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not args.keep:
        with psycopg.connect(conninfo) as conn:
            conn.execute("DELETE FROM issue_embedding WHERE model_id = %s", (key,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
