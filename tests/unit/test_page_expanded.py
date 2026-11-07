"""Expanded coverage for the search page (story 1.7, epic R4).

Fills gaps left by `test_page.py`: the renderer's pure functions (URL safety, kind labels,
outcome ref and summary, message roles), form-body parsing edge cases, the k=10 cap and
score order, routing boundaries around `/`, and the chart's Exact `/` HTTPRoute match.
"""

import shutil
import subprocess
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from tests.target import REPO, TARGET_QUERY
from tests.unit.test_page import FORM, OUTCOMES, Parsed, parse
from ticketscope.contract.search import Issue, Outcome, SearchResult
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.http import page
from ticketscope.http.app import PAGE_K, create_app
from ticketscope.settings import Settings

CHART = REPO / "deploy" / "charts" / "ticketscope"


def _result(
    *,
    rank: int = 1,
    title: str = "Pods stall",
    url: str = "https://bugs.example.test/1",
    kind: str = "short",
    status: str = "fixed",
    summary: str | None = "Fixed in 1.2",
    ref: str | None = None,
) -> SearchResult:
    return SearchResult.model_validate(
        {
            "rank": rank,
            "score": 1.0,
            "issue": Issue.model_validate(
                {"number": rank, "title": title, "url": url, "kind": kind, "state": "closed"}
            ).model_dump(),
            "outcome": Outcome.model_validate(
                {"status": status, "summary": summary, "source": "label", "ref": ref}
            ).model_dump(),
        }
    )


def _record(number: int, **over: object) -> IssueRecord:
    fields: dict[str, object] = {
        "number": number,
        "title": f"issue {number}",
        "url": f"https://bugs.example.test/{number}",
        "kind": "short",
        "state": "closed",
        "outcome_status": "fixed",
    }
    fields.update(over)
    return IssueRecord(**fields)  # pyright: ignore[reportArgumentType]


def _client(*docs: tuple[IssueRecord, str]) -> TestClient:
    store = InMemoryCorpusStore(docs, corpus_version="v")
    return TestClient(create_app(store=store, settings=Settings(default_mode="keyword")))


def _post_raw(client: TestClient, body: bytes | str) -> Parsed:
    response = client.post("/", content=body, headers=FORM)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    return parse(response.text)


# --- renderer: pure functions -------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "linked"),
    [
        ("https://bugs.example.test/1", True),
        ("http://bugs.example.test/1", True),
        ("javascript:alert(1)", False),
        ("data:text/html,<b>x</b>", False),
        ("//evil.example.test/x", False),
        ("/relative/path", False),
        (" https://leading-space.test", False),
        ("", False),
    ],
)
def test_only_http_and_https_urls_become_links(url: str, linked: bool) -> None:
    html = page.render("q", [_result(url=url)])
    row = parse(html).rows[0]
    assert (row.href is not None) is linked
    if linked:
        assert row.href == url
    assert row.title == "Pods stall"


def test_href_attribute_is_quote_escaped() -> None:
    url = 'https://x.test/"onmouseover="alert(1)'
    html = page.render("q", [_result(url=url)])
    assert '"onmouseover="' not in html
    assert "&quot;onmouseover=&quot;" in html
    assert parse(html).rows[0].href == url


@pytest.mark.parametrize(("kind", "label"), [("short", "short"), ("log_heavy", "log-heavy")])
def test_kind_is_shown_with_its_label(kind: str, label: str) -> None:
    assert parse(page.render("q", [_result(kind=kind)])).rows[0].kind == label


@pytest.mark.parametrize("status", sorted(OUTCOMES))
def test_every_outcome_status_is_in_the_attribute_and_the_badge(status: str) -> None:
    row = parse(page.render("q", [_result(status=status)])).rows[0]
    assert row.outcome_attr == row.outcome == status


def test_null_summary_has_no_summary_element() -> None:
    html = page.render("q", [_result(summary=None)])
    assert 'class="summary"' not in html
    assert parse(html).rows[0].summary is None


def test_http_ref_is_a_link_and_other_refs_are_text() -> None:
    linked = page.render("q", [_result(ref="https://bugs.example.test/MC-9")])
    assert '<a class="ref" href="https://bugs.example.test/MC-9">' in linked
    plain = page.render("q", [_result(ref="MC-9 <b>")])
    assert '<span class="ref">MC-9 &lt;b&gt;</span>' in plain
    assert 'class="ref" href' not in plain


@pytest.mark.parametrize("ref", [None, ""])
def test_missing_ref_renders_no_ref_element(ref: str | None) -> None:
    assert 'class="ref"' not in page.render("q", [_result(ref=ref)])


def test_rows_keep_the_given_rank_order() -> None:
    results = [_result(rank=n, title=f"t{n}") for n in (1, 2, 3)]
    rows = parse(page.render("q", results)).rows
    assert [(r.rank, r.title) for r in rows] == [(1, "t1"), (2, "t2"), (3, "t3")]


def test_error_message_is_an_alert_and_info_is_a_status() -> None:
    error = page.render("q", message=page.ERROR_MESSAGE, error=True)
    assert '<p class="message error" role="alert">' in error
    info = page.render("q", message=page.NO_MATCH_MESSAGE)
    assert '<p class="message" role="status">' in info
    assert "error" not in info.split("<main>", 1)[1]


def test_results_page_has_no_message_and_empty_results_have_no_list() -> None:
    with_rows = parse(page.render("q", [_result()]))
    assert with_rows.messages == []
    assert "<ol" not in page.render("q", [])
    assert "<ol" not in page.render("q", None, page.NO_MATCH_MESSAGE)


def test_textarea_cannot_be_closed_by_the_query() -> None:
    query = "</textarea><script>alert(1)</script>"
    html = page.render(query)
    assert html.count("</textarea>") == 1
    assert "<script" not in html
    assert parse(html).textarea == query


def test_message_text_is_escaped() -> None:
    html = page.render("q", message="<b>hi</b>")
    assert "&lt;b&gt;hi&lt;/b&gt;" in html
    assert parse(html).messages == ["<b>hi</b>"]


# --- form-body parsing through the app ----------------------------------------------------


@pytest.fixture
def client(fixture_store: InMemoryCorpusStore) -> TestClient:
    return TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))


@pytest.mark.parametrize("body", ["", "other=1", "q"], ids=["empty-body", "no-q", "bare-q"])
def test_post_without_a_q_value_is_the_blank_prompt(client: TestClient, body: str) -> None:
    parsed = _post_raw(client, body)
    assert parsed.messages == [page.BLANK_MESSAGE]
    assert parsed.rows == []
    assert parsed.textarea == ""


def test_plus_and_percent_escapes_are_decoded(client: TestClient) -> None:
    raw = "q=" + TARGET_QUERY.replace(" ", "+").replace("eviction", "evi%63tion")
    parsed = _post_raw(client, raw)
    assert parsed.textarea == TARGET_QUERY
    assert parsed.rows


def test_invalid_utf8_in_the_body_does_not_fail(client: TestClient) -> None:
    parsed = _post_raw(client, b"q=zephyrcache+%FF%FE+eviction")
    assert parsed.rows
    assert parsed.textarea is not None
    assert parsed.textarea.startswith("zephyrcache ")


def test_non_ascii_query_echoes_exactly(client: TestClient) -> None:
    query = "zephyrcache — éviction 驱逐 🚀"
    parsed = _post_raw(client, urlencode({"q": query}))
    assert parsed.textarea == query


def test_crlf_in_a_pasted_log_echoes_exactly(client: TestClient) -> None:
    query = "zephyrcache eviction\r\n\tat a.b(C.java:1)\r\n"
    response = client.post("/", content=urlencode({"q": query}), headers=FORM)
    # Browsers normalise CRLF in a textarea; the body carries it as written.
    assert "zephyrcache eviction\r\n\tat a.b(C.java:1)\r\n</textarea>" in response.text


# --- retrieval through the page -----------------------------------------------------------


def test_page_lists_at_most_k_rows_in_score_order() -> None:
    assert PAGE_K == 10
    docs = [(_record(n), "quokka " * n) for n in range(1, 14)]
    client = _client(*docs)
    rows = _post_raw(client, urlencode({"q": "quokka"})).rows
    assert len(rows) == PAGE_K
    assert [r.rank for r in rows] == list(range(1, PAGE_K + 1))
    # Highest term count ranks first: issue 13 down to issue 4.
    assert [r.title for r in rows] == [f"issue {n}" for n in range(13, 3, -1)]


def test_page_rows_carry_ref_and_null_summary_from_the_store() -> None:
    issue = _record(
        7,
        kind="log_heavy",
        outcome_status="duplicate",
        outcome_summary=None,
        outcome_source="linked_pr",
        outcome_ref="https://bugs.example.test/MC-1",
    )
    response = _client((issue, "quokka")).post("/", content="q=quokka", headers=FORM)
    [row] = parse(response.text).rows
    assert (row.kind, row.outcome_attr, row.summary) == ("log-heavy", "duplicate", None)
    assert 'href="https://bugs.example.test/MC-1"' in response.text


def test_page_ignores_the_settings_default_mode(fixture_store: InMemoryCorpusStore) -> None:
    # The page always uses keyword retrieval, whatever the API default is.
    client = TestClient(create_app(store=fixture_store, settings=Settings(default_mode="nope")))
    assert _post_raw(client, urlencode({"q": TARGET_QUERY})).rows


# --- routing boundaries -------------------------------------------------------------------


def test_page_routes_do_not_shadow_other_paths(client: TestClient) -> None:
    assert client.get("/healthz").status_code == 200
    missing = client.get("/nope")
    assert missing.status_code == 404
    assert not missing.headers["content-type"].startswith("text/html")


def test_other_methods_on_the_page_are_405(client: TestClient) -> None:
    response = client.put("/", content="q=x", headers=FORM)
    assert response.status_code == 405
    assert "GET" in response.headers["allow"]


@pytest.mark.xfail(
    strict=True,
    reason="product defect: GET / and POST / are separate routes, so a 405 on / lists only"
    " GET in Allow (RFC 9110 15.5.6 says Allow lists the supported methods)",
)
def test_405_on_the_page_lists_both_page_methods(client: TestClient) -> None:
    response = client.put("/", content="q=x", headers=FORM)
    assert set(response.headers["allow"].replace(" ", "").split(",")) == {"GET", "POST"}


# --- chart: Exact / on the api HTTPRoute (AD-14) ------------------------------------------


@pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")
def test_api_route_matches_exact_root_and_v1_prefix_only() -> None:
    result = subprocess.run(
        [
            "helm",
            "template",
            "t",
            str(CHART),
            "--set-string",
            "image.app.tag=t",
            "--set-string",
            "image.postgres.tag=18-t",
            # Backups need an environment's destinationPath (story 8).
            "--set",
            "backup.enabled=false",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    [route] = [
        d
        for d in result.stdout.split("\n---\n")
        if "kind: HTTPRoute" in d and "name: ticketscope-api\n" in d
    ]
    flat = " ".join(route.split())
    assert "path: type: PathPrefix value: /v1" in flat
    assert "path: type: Exact value: /" in flat
    assert "type: PathPrefix value: / " not in flat + " "
