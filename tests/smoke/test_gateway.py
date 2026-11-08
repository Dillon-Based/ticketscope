"""Smoke and load checks against the kind cluster on the pinned snapshot (marker `kind`).

Needs `TICKETSCOPE_GATEWAY_URL` (e.g. `http://172.18.0.5`) and
`TICKETSCOPE_GATEWAY_HOST` (the route hostname), plus `kubectl` and `helm` on the cluster.
Run with `uv run pytest -m kind tests/smoke`. The tests run in file order: (1) search
through the Gateway, (1b) the rest of the /v1 contract through the Gateway, (1c) the
search page through the Gateway, (2) SQL on the CNPG primary, (3) the load report, forcing
a reload when the newest load was a no-op, (4) a same-pin upgrade is a no-op, (5) a stale
preprocessing version reloads, (6) two ready instances, (6b) platform and app upgrades
keep the backup TLS and credentials, (7) an on-demand backup completes to SeaweedFS, (8)
one search yields one AD-10 trace in Tempo, (8b) the same trace through Grafana's Tempo
datasource.
"""

import base64
import json
import os
import re
import secrets
import socket
import subprocess
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlencode

import httpx2
import pytest

from tests.factories import form_payload, search_payload
from tests.target import NO_MATCH_QUERY, REPO, snapshot_pin
from tests.waiting import eventually, wait_for_output
from ticketscope.contract.search import IssueResponse, Problem, SearchResponse
from ticketscope.core.derive import preprocessing_version

pytestmark = pytest.mark.kind

NAMESPACE = os.environ.get("TICKETSCOPE_NAMESPACE", "ticketscope")
CLUSTER = os.environ.get("TICKETSCOPE_CLUSTER_NAME", "ticketscope-db")
PLATFORM_NAMESPACE = os.environ.get("TICKETSCOPE_PLATFORM_NAMESPACE", "platform")
BACKUP_BUCKET = "ticketscope-backups"  # backup.destinationPath in values-kind.yaml
BACKUP_TIMEOUT_SECONDS = 600
PIN = snapshot_pin()["version"]
GOLDEN = json.loads((REPO / "eval" / "golden-queries.json").read_text(encoding="utf-8"))
ISSUE_COUNT = 32153  # issues in snapshot 2026.11.1
RESULTS_QUERY = "launcher crash"
OUTCOMES = ("fixed", "duplicate", "not_planned", "stale", "answered", "unknown")


def _gateway() -> tuple[str, str]:
    url = os.environ.get("TICKETSCOPE_GATEWAY_URL")
    host = os.environ.get("TICKETSCOPE_GATEWAY_HOST")
    if not url or not host:
        pytest.fail("TICKETSCOPE_GATEWAY_URL and TICKETSCOPE_GATEWAY_HOST must be set")
    return url.rstrip("/"), host


def _post_search(payload: dict[str, object]) -> httpx2.Response:
    url, host = _gateway()
    return httpx2.post(f"{url}/v1/search", json=payload, headers={"Host": host}, timeout=30)


def _search(query: str) -> SearchResponse:
    response = _post_search(search_payload(query, mode="keyword"))
    assert response.status_code == 200, response.text
    return SearchResponse.model_validate(response.json())


def _get_issue(number: int) -> httpx2.Response:
    url, host = _gateway()
    return httpx2.get(f"{url}/v1/issues/{number}", headers={"Host": host}, timeout=30)


def _assert_problem(response: httpx2.Response, status: int) -> Problem:
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = Problem.model_validate(response.json())
    assert (problem.type, problem.status) == ("about:blank", status)
    assert problem.title and problem.detail
    return problem


def _kubectl(*args: str) -> str:
    return subprocess.run(
        ["kubectl", "-n", NAMESPACE, *args], check=True, capture_output=True, text=True
    ).stdout


def _sql(statement: str) -> str:
    """Run `statement` with psql on the CNPG primary; return its unaligned output."""
    pod = _kubectl(
        "get",
        "pod",
        "-l",
        f"cnpg.io/cluster={CLUSTER},cnpg.io/instanceRole=primary",
        "-o",
        "jsonpath={.items[0].metadata.name}",
    ).strip()
    assert pod, "no CNPG primary pod"
    return _kubectl("exec", pod, "-c", "postgres", "--", "psql", "-d", "app", "-tAc", statement)


def _corpus_meta() -> tuple[str, str, str]:
    """`snapshot_version|embedding_model_id|preprocessing_version` (NULL reads as '')."""
    row = _sql(
        "SELECT snapshot_version, coalesce(embedding_model_id, ''),"
        " coalesce(preprocessing_version, '') FROM corpus_meta"
    ).strip()
    version, model, pre = row.split("|")
    return version, model, pre


def _load_log() -> str:
    """The log of the load Job's Succeeded pod (newest if several): with `backoffLimit`,
    `kubectl logs job/...` may pick a failed attempt."""
    pods = _kubectl(
        "get",
        "pod",
        "-l",
        "job-name=ticketscope-load",
        "--field-selector",
        "status.phase=Succeeded",
        "--sort-by",
        ".metadata.creationTimestamp",
        "-o",
        "jsonpath={.items[*].metadata.name}",
    ).split()
    assert pods, "no Succeeded ticketscope-load pod"
    return _kubectl("logs", pods[-1])


def _upgrade() -> None:
    """A Helm upgrade with the same values: re-runs migrate and load as hooks."""
    subprocess.run(
        [
            "helm",
            "upgrade",
            "ticketscope",
            str(REPO / "deploy" / "charts" / "ticketscope"),
            "-n",
            NAMESPACE,
            "--reuse-values",
            "--timeout",
            "15m",
        ],
        check=True,
    )


def _force_reload() -> tuple[str, tuple[str, str, str]]:
    """Mark `corpus_meta` stale and upgrade, so the load Job reloads.

    Returns the load log and `corpus_meta` right after that upgrade. Never leaves
    `corpus_meta` stale: if the reload did not make it current, one more upgrade does.
    """
    current = (PIN, "", preprocessing_version())
    _sql("UPDATE corpus_meta SET preprocessing_version = 'pre0.stale'")
    try:
        _upgrade()
        return _load_log(), _corpus_meta()
    finally:
        if _corpus_meta() != current:
            _upgrade()


# (1) ---------------------------------------------------------------------------------------


def test_search_serves_the_pinned_snapshot_with_outcomes() -> None:
    body = _search(RESULTS_QUERY)
    assert body.mode == "keyword"
    assert body.score_kind == "bm25"
    assert body.corpus_version == PIN
    assert body.results, "no results"
    assert [r.rank for r in body.results] == list(range(1, len(body.results) + 1))
    scores = [r.score for r in body.results]
    assert scores == sorted(scores, reverse=True)
    assert all(r.outcome.status in OUTCOMES for r in body.results)
    assert any(r.outcome.status != "unknown" for r in body.results)


def test_no_match_is_empty_through_the_gateway() -> None:
    body = _search(NO_MATCH_QUERY)
    assert body.corpus_version == PIN
    assert body.results == []


# (1b) --------------------------------------------------------------------------------------


def test_issue_detail_matches_the_search_hit() -> None:
    top = _search(RESULTS_QUERY).results[0]
    response = _get_issue(top.issue.number)
    assert response.status_code == 200, response.text
    body = IssueResponse.model_validate(response.json())
    assert body.issue.number == top.issue.number
    assert body.issue.body, "empty body"
    assert body.outcome == top.outcome


def test_unknown_issue_is_a_404_problem() -> None:
    problem = _assert_problem(_get_issue(1), 404)
    assert "1" in problem.detail


@pytest.mark.parametrize(
    "payload",
    [
        search_payload(RESULTS_QUERY, mode="keyword", k=0),
        search_payload(RESULTS_QUERY, mode="keyword", k=51),
        search_payload(RESULTS_QUERY, mode="nope"),
    ],
    ids=["k=0", "k=51", "mode=nope"],
)
def test_invalid_search_is_a_422_problem(payload: dict[str, object]) -> None:
    problem = _assert_problem(_post_search(payload), 422)
    assert problem.errors


def test_operator_characters_rank() -> None:
    # Golden's independently recorded vague twin is rank 5 on this pinned corpus.
    entry = next(q for q in GOLDEN["queries"] if q["id"] == "vague")
    body = _search(str(entry["query"]) + ' & | (:!) !! "')
    assert int(entry["expected_issue"]["number"]) in [r.issue.number for r in body.results]


def test_a_pasted_log_in_a_4kb_request_ranks() -> None:
    entry = next(q for q in GOLDEN["queries"] if q["id"] == "log-heavy")
    # Preserve the independently recorded log/twin oracle (rank 9) while exercising
    # a >=4KB wire input. Whitespace padding introduces no extra ranking tokens.
    query = str(entry["query"]).ljust(4096)
    assert len(query.encode()) >= 4096
    body = _search(query)
    assert int(entry["expected_issue"]["number"]) in [r.issue.number for r in body.results]


# (1c) --------------------------------------------------------------------------------------


class _Rows(HTMLParser):
    """`(rank, data-outcome, title href, kind text, outcome text)` per result row, plus
    whether the page has the `q` textarea in a post form."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, str]] = []
        self.has_form = False
        self._capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        css = a.get("class", "").split()
        if tag == "textarea" and a.get("name") == "q":
            self.has_form = True
        elif tag == "li" and "result" in css:
            self.rows.append(
                {"rank": a["data-rank"], "data-outcome": a["data-outcome"], "href": ""}
            )
        elif self.rows and {"title", "kind", "outcome"} & set(css):
            name = ({"title", "kind", "outcome"} & set(css)).pop()
            if name == "title":
                self.rows[-1]["href"] = a.get("href", "")
            self.rows[-1].setdefault(name, "")
            self._capture = name

    def handle_endtag(self, tag: str) -> None:
        self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self.rows[-1][self._capture] += data


def _page(query: str) -> tuple[httpx2.Response, _Rows]:
    url, host = _gateway()
    response = httpx2.post(
        f"{url}/",
        content=urlencode(form_payload(query)),
        headers={"Host": host, "content-type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/html")
    parsed = _Rows()
    parsed.feed(response.text)
    return response, parsed


def test_page_serves_the_form() -> None:
    url, host = _gateway()
    response = httpx2.get(f"{url}/", headers={"Host": host}, timeout=30)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/html")
    parsed = _Rows()
    parsed.feed(response.text)
    assert parsed.has_form
    assert '<form method="post" action="/">' in response.text


@pytest.mark.parametrize("entry", GOLDEN["queries"], ids=[q["id"] for q in GOLDEN["queries"]])
def test_page_renders_each_golden_query(entry: dict[str, object]) -> None:
    _, parsed = _page(str(entry["query"]))
    assert parsed.rows, "no rows"
    assert [int(r["rank"]) for r in parsed.rows] == list(range(1, len(parsed.rows) + 1))
    for row in parsed.rows:
        assert row["href"].startswith("https://"), row
        assert row.get("title", "").strip(), row
        assert row.get("kind") in ("short", "log-heavy"), row
        assert row["data-outcome"] in OUTCOMES, row
        assert row.get("outcome", "").strip() == row["data-outcome"], row


def test_page_escapes_a_script_query() -> None:
    response, _ = _page("<script>alert(1)</script> launcher crash")
    assert "<script" not in response.text
    assert "&lt;script&gt;" in response.text


# (2) ---------------------------------------------------------------------------------------


def test_every_issue_is_loaded_with_a_kind_and_an_outcome() -> None:
    assert int(_sql("SELECT count(*) FROM issue")) == ISSUE_COUNT
    missing = _sql(
        "SELECT count(*) FROM issue WHERE coalesce(kind, '') = ''"
        " OR coalesce(outcome_status, '') = ''"
    )
    assert int(missing) == 0
    assert int(_sql("SELECT count(DISTINCT outcome_status) FROM issue")) > 1
    assert _corpus_meta() == (PIN, "", preprocessing_version())


def test_api_database_role_can_read_but_cannot_write() -> None:
    """[P1] Exercise AD-7 using the API container's actual configured credentials.

    No secret leaves the pod. Zero-row statements and rollback make an unexpected
    grant safe to diagnose without changing the pinned corpus.
    """
    script = """
import psycopg
from ticketscope.settings import Settings

with psycopg.connect(Settings().conninfo()) as conn:
    user, count = conn.execute("SELECT current_user, count(*) FROM issue").fetchone()
    assert user == "ticketscope_ro", "API is not connected as ticketscope_ro"
    assert count > 0, "API role cannot read the loaded corpus"
    conn.rollback()
    for operation, statement in (
        ("INSERT", "INSERT INTO issue SELECT * FROM issue WHERE false"),
        ("UPDATE", "UPDATE issue SET title = title WHERE false"),
        ("DELETE", "DELETE FROM issue WHERE false"),
    ):
        try:
            conn.execute(statement)
        except psycopg.errors.InsufficientPrivilege as error:
            assert error.sqlstate == "42501"
            conn.rollback()
        else:
            conn.rollback()
            raise AssertionError(operation + " unexpectedly permitted")
print("ticketscope_ro: SELECT allowed; INSERT UPDATE DELETE denied")
"""
    result = subprocess.run(
        [
            "kubectl",
            "-n",
            NAMESPACE,
            "exec",
            "deploy/ticketscope-api",
            "-c",
            "api",
            "--",
            "python",
            "-c",
            script,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"API role privilege check failed: {result.stderr}"
    assert result.stdout.strip() == "ticketscope_ro: SELECT allowed; INSERT UPDATE DELETE denied"


# (3) ---------------------------------------------------------------------------------------


def test_load_log_has_the_report() -> None:
    log = _load_log()
    if "load report:" not in log:
        # The newest load was a no-op (e.g. right after an in-place `kind-up.sh` upgrade),
        # so it logged no report: force a reload to get a fresh one.
        assert "no-op" in log, log
        log, meta = _force_reload()
        assert meta == (PIN, "", preprocessing_version())
    reports = [line for line in log.splitlines() if "load report:" in line]
    assert reports, "no load report line"
    line = reports[-1]
    assert f"issues={ISSUE_COUNT}" in line
    kinds = dict(re.findall(r"kind\.(\w+)=([\d.]+)%", line))
    assert set(kinds) == {"short", "log_heavy"}
    outcomes = dict(re.findall(r"outcome\.(\w+)=([\d.]+)%", line))
    assert set(outcomes) == set(OUTCOMES)
    assert "budget_seconds=600" in line
    assert "within_budget=true" in line


# (4) ---------------------------------------------------------------------------------------


def test_upgrade_with_the_same_pin_is_a_no_op() -> None:
    _upgrade()
    log = _load_log()
    assert "no-op" in log, log
    assert "load report:" not in log
    assert _search(RESULTS_QUERY).corpus_version == PIN


# (5) ---------------------------------------------------------------------------------------


def test_stale_preprocessing_version_reloads() -> None:
    log, meta = _force_reload()
    assert "reloading" in log and "preprocessing_version" in log, log
    assert "load report:" in log
    assert meta == (PIN, "", preprocessing_version())


# (6) ---------------------------------------------------------------------------------------


def test_cluster_has_two_ready_instances() -> None:
    out = _kubectl("get", "clusters.postgresql.cnpg.io", CLUSTER, "-o", "json")
    status = json.loads(out)["status"]
    assert status.get("readyInstances") == 2, status


def test_cluster_runs_both_extensions_on_persistent_volumes() -> None:
    """R5: pgvector and pg_textsearch are installed in the app database, and each of the
    two instances keeps its data on a bound PersistentVolumeClaim."""
    extensions = set(_sql("SELECT extname FROM pg_extension").split())
    assert {"vector", "pg_textsearch"} <= extensions, extensions
    claims = json.loads(_kubectl("get", "pvc", "-l", f"cnpg.io/cluster={CLUSTER}", "-o", "json"))
    bound = [c["metadata"]["name"] for c in claims["items"] if c["status"].get("phase") == "Bound"]
    assert len(bound) >= 2, f"bound PVCs for {CLUSTER}: {bound}"


# (6b) --------------------------------------------------------------------------------------

_KEPT_SECRETS = (
    (PLATFORM_NAMESPACE, "barman-cloud-server-tls"),
    (PLATFORM_NAMESPACE, "barman-cloud-client-tls"),
    (PLATFORM_NAMESPACE, "seaweedfs-s3-secret"),
    (NAMESPACE, "ticketscope-backup-s3"),
)


def _secret_data(namespace: str, name: str) -> dict[str, str]:
    out = subprocess.run(
        ["kubectl", "-n", namespace, "get", "secret", name, "-o", "jsonpath={.data}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    data: dict[str, str] = json.loads(out or "{}")
    return data


def test_upgrades_keep_the_backup_tls_and_credentials() -> None:
    before = {s: _secret_data(*s) for s in _KEPT_SECRETS}
    assert all(before.values()), before.keys()
    subprocess.run(
        [
            "helm",
            "upgrade",
            "platform",
            str(REPO / "deploy" / "charts" / "platform"),
            "-n",
            PLATFORM_NAMESPACE,
            "--reuse-values",
            "--wait",
            "--timeout",
            "10m",
        ],
        check=True,
    )
    _upgrade()
    after = {s: _secret_data(*s) for s in _KEPT_SECRETS}
    for secret in _KEPT_SECRETS:
        assert after[secret] == before[secret], secret


# (7) ---------------------------------------------------------------------------------------


def _backup_status(name: str) -> dict[str, object]:
    out = _kubectl("get", "backups.postgresql.cnpg.io", name, "-o", "json")
    status: dict[str, object] = json.loads(out).get("status", {})
    return status


def _bucket_listing(path: str) -> list[str]:
    """Entry names under `path` in the backup bucket, from the SeaweedFS filer's JSON
    listing, read inside the all-in-one pod (SeaweedFS is never exposed, AD-14)."""
    result = subprocess.run(
        [
            "kubectl",
            "-n",
            PLATFORM_NAMESPACE,
            "exec",
            "deploy/seaweedfs-all-in-one",
            "--",
            "curl",
            "-sSf",
            "-H",
            "Accept: application/json",
            f"http://localhost:8888/buckets/{BACKUP_BUCKET}/{path.strip('/')}/?limit=1000",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"listing {path}: {result.stdout}{result.stderr}"
    entries = json.loads(result.stdout).get("Entries") or []
    return [str(e["FullPath"]).rsplit("/", 1)[-1] for e in entries]


def _assert_on_demand_backup_completes(label: str = "smoke") -> None:
    """Apply an on-demand plugin Backup named for `label`, wait for it to complete and
    check its base backup is in the SeaweedFS bucket; shared with the integrated check."""
    name = f"{CLUSTER}-{label}-{int(time.time())}"
    manifest = {
        "apiVersion": "postgresql.cnpg.io/v1",
        "kind": "Backup",
        "metadata": {"name": name, "namespace": NAMESPACE},
        "spec": {
            "cluster": {"name": CLUSTER},
            "method": "plugin",
            "pluginConfiguration": {"name": "barman-cloud.cloudnative-pg.io"},
        },
    }
    applied = subprocess.run(
        ["kubectl", "-n", NAMESPACE, "apply", "-f", "-"],
        input=json.dumps(manifest),
        check=False,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0, f"apply Backup: {applied.stdout}{applied.stderr}"
    # Watch emits the current object and subsequent changes; failed backups fail
    # immediately rather than waiting for a completion-only condition to time out.
    watch = subprocess.Popen(
        [
            "kubectl",
            "-n",
            NAMESPACE,
            "get",
            "backups.postgresql.cnpg.io",
            name,
            "--watch",
            "-o",
            'jsonpath={.status.phase}{"\\n"}',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        phase = wait_for_output(
            watch, lambda line: line in {"completed", "failed"}, timeout=BACKUP_TIMEOUT_SECONDS
        )
        status = _backup_status(name)
        assert phase == "completed", f"backup failed: {status}"
        assert status.get("phase") == "completed", status
    finally:
        watch.terminate()
        watch.wait(timeout=10)
    backup_id = str(status.get("backupId") or "")
    assert backup_id, status
    # The ObjectStore's serverName defaults to the Cluster's name.
    server = str(status.get("serverName") or CLUSTER)
    listing = _bucket_listing(f"{server}/base/{backup_id}")
    assert "backup.info" in listing, listing
    assert any(n.startswith("data.tar") for n in listing), listing
    # Deleted only on success: a failed Backup stays for the Diagnostics step.
    subprocess.run(
        ["kubectl", "-n", NAMESPACE, "delete", "backups.postgresql.cnpg.io", name],
        check=False,
        capture_output=True,
    )


def test_on_demand_backup_completes_to_seaweedfs() -> None:
    _assert_on_demand_backup_completes()


# (8) ---------------------------------------------------------------------------------------

TRACE_TIMEOUT_SECONDS = 60
TRACE_QUERY = str(GOLDEN["queries"][0]["query"])


def _attributes(item: dict[str, Any]) -> dict[str, Any]:
    """OTLP JSON attributes as a plain dict (`intValue` arrives as a string)."""
    out: dict[str, Any] = {}
    for attribute in item.get("attributes") or []:
        value: dict[str, Any] = attribute.get("value") or {}
        if "intValue" in value:
            out[attribute["key"]] = int(value["intValue"])
        elif value:
            out[attribute["key"]] = next(iter(value.values()))
    return out


def _spans(trace: dict[str, Any]) -> list[dict[str, Any]]:
    """Every span of a Tempo `/api/v2/traces` body, with its resource's `service.name`."""
    body: dict[str, Any] = trace.get("trace", trace)
    spans: list[dict[str, Any]] = []
    for resource_spans in body.get("resourceSpans") or []:
        service = _attributes(resource_spans.get("resource") or {}).get("service.name")
        for scope_spans in resource_spans.get("scopeSpans") or []:
            for span in scope_spans.get("spans") or []:
                spans.append({**span, "service": service, "attrs": _attributes(span)})
    return spans


_KINDS = {"1": "INTERNAL", "2": "SERVER", "3": "CLIENT"}


def _kind(span: dict[str, Any]) -> str:
    """`SPAN_KIND_SERVER` or a bare enum number, as `SERVER`."""
    kind = str(span.get("kind", ""))
    return _KINDS.get(kind, kind.removeprefix("SPAN_KIND_"))


def _assert_ad10_tree(trace: dict[str, Any]) -> None:
    """SERVER `POST /v1/search` -> INTERNAL `retrieval keyword` -> psycopg CLIENT.
    Span ids are compared as returned (base64 or hex), within this one response."""
    spans = _spans(trace)
    servers = [
        s
        for s in spans
        if s["service"] == "ticketscope-api"
        and _kind(s) == "SERVER"
        and s.get("name") == "POST /v1/search"
    ]
    assert len(servers) == 1, spans
    server = servers[0]
    [retrieval] = [s for s in spans if s.get("name") == "retrieval keyword"]
    assert retrieval["service"] == "ticketscope-api"
    assert _kind(retrieval) == "INTERNAL"
    assert retrieval.get("parentSpanId") == server["spanId"]
    attrs = retrieval["attrs"]
    assert attrs["gen_ai.operation.name"] == "retrieval"
    assert attrs["gen_ai.data_source.id"] == "ticketscope-mojang-jira"
    assert attrs["ticketscope.retrieval.mode"] == "keyword"
    assert attrs["ticketscope.retrieval.k"] == 10
    assert attrs["ticketscope.corpus.version"] == PIN
    assert attrs["ticketscope.result.count"] >= 1
    # No query text on any span (not opted in).
    query = TRACE_QUERY.lower()
    for span in spans:
        assert not any(query in str(v).lower() for v in span["attrs"].values()), span
    db = [
        s
        for s in spans
        if _kind(s) == "CLIENT"
        and s["attrs"].get("db.system.name") == "postgresql"
        and s.get("parentSpanId") == retrieval["spanId"]
    ]
    assert db, spans


def _poll_trace(fetch: Callable[[], tuple[int, str]]) -> dict[str, Any]:
    """Poll `fetch` (status, body) until the trace has the full AD-10 tree."""

    def complete_trace() -> dict[str, Any]:
        status, body = fetch()
        assert status == 200, f"trace not complete: last {status}: {body[:2000]}"
        try:
            trace: dict[str, Any] = json.loads(body)
            _assert_ad10_tree(trace)
        except (KeyError, ValueError) as error:
            raise AssertionError(f"incomplete trace: {body[:2000]}") from error
        return trace

    return eventually(complete_trace, timeout=TRACE_TIMEOUT_SECONDS, interval=3)


def _search_with_traceparent() -> str:
    """POST one golden query with a fresh `traceparent`; return its trace id (hex)."""
    trace_id = secrets.token_hex(16)
    parent_id = secrets.token_hex(8)
    url, host = _gateway()
    response = httpx2.post(
        f"{url}/v1/search",
        json=search_payload(TRACE_QUERY, mode="keyword", k=10),
        headers={"Host": host, "traceparent": f"00-{trace_id}-{parent_id}-01"},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    assert SearchResponse.model_validate(response.json()).results, "no results"
    return trace_id


@pytest.fixture(scope="module")
def traced_search_id() -> str:
    """One traced search per module, shared by (8) and (8b); pytest owns its lifetime."""
    return _search_with_traceparent()


def _tempo(trace_id: str) -> tuple[int, str]:
    """Tempo's trace-by-id through the API server's service proxy (Tempo is not exposed)."""
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "--raw",
            f"/api/v1/namespaces/{PLATFORM_NAMESPACE}/services/tempo:3200/proxy"
            f"/api/v2/traces/{trace_id}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return 200, result.stdout
    return 404 if "NotFound" in result.stderr else 0, result.stdout + result.stderr


def test_one_search_yields_one_trace_in_tempo(traced_search_id: str) -> None:
    trace_id = traced_search_id
    _poll_trace(lambda: _tempo(trace_id))


# (8b) --------------------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _grafana() -> Iterator[str]:
    """A port-forward to Grafana (never exposed, AD-14); yields its base URL."""
    port = _free_port()
    forward = subprocess.Popen(
        [
            "kubectl",
            "-n",
            PLATFORM_NAMESPACE,
            "port-forward",
            "svc/grafana",
            f"{port}:80",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        wait_for_output(forward, lambda line: line.startswith("Forwarding from "), timeout=30)

        def healthy() -> None:
            assert forward.poll() is None, "Grafana port-forward exited"
            try:
                response = httpx2.get(f"{base}/api/health", timeout=5)
            except httpx2.HTTPError as error:
                raise AssertionError("Grafana health endpoint unavailable") from error
            assert response.status_code == 200, response.text

        eventually(healthy, timeout=30, interval=1)
        yield base
    finally:
        forward.terminate()
        forward.wait(timeout=10)


def test_the_trace_is_served_by_grafanas_tempo_datasource(traced_search_id: str) -> None:
    trace_id = traced_search_id
    secret = _secret_data(PLATFORM_NAMESPACE, "grafana")
    user = base64.b64decode(secret["admin-user"]).decode()
    password = base64.b64decode(secret["admin-password"]).decode()
    with _grafana() as base:

        def fetch() -> tuple[int, str]:
            response = httpx2.get(
                f"{base}/api/datasources/proxy/uid/tempo/api/v2/traces/{trace_id}",
                auth=(user, password),
                timeout=30,
            )
            return response.status_code, response.text

        _poll_trace(fetch)


# (8c) --------------------------------------------------------------------------------------


def _api_log_lines() -> list[str]:
    """Recent log lines of every api pod (one replica today; the selector keeps it right)."""
    out = _kubectl("logs", "-l", "app.kubernetes.io/component=api", "--since=10m", "--tail=-1")
    return [line for line in out.splitlines() if line.strip()]


@pytest.mark.criterion("ticketscope--e1-s9--AC-3")
def test_api_logs_are_json_lines_carrying_the_request_trace_id() -> None:
    """Story 9 AC-3 on the deployed pod: every api log line is a JSON object, and the
    lines logged for a traced search carry that request's trace id."""
    trace_id = _search_with_traceparent()

    def request_lines() -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for line in _api_log_lines():
            try:
                record = json.loads(line)
            except ValueError as error:
                raise AssertionError(f"api log line is not JSON: {line[:500]}") from error
            assert isinstance(record, dict), f"api log line is not a JSON object: {line[:500]}"
            records.append(record)
        mine = [r for r in records if r.get("trace_id") == trace_id]
        assert mine, f"no api log line carries trace_id {trace_id}"
        return mine

    mine = eventually(request_lines, timeout=30, interval=2)
    assert any("POST /v1/search" in str(r.get("message")) for r in mine), mine
    assert all(r.get("span_id") for r in mine), mine
