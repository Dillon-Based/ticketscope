"""The search page's I/O matrix through `create_app`, with the fake store injected (R4)."""

import ast
import html
import logging
import sys
import typing
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlencode

import httpx2
import pytest
from fastapi.testclient import TestClient

from tests.target import NO_MATCH_QUERY, REPO, TARGET_NUMBER, TARGET_QUERY
from tests.unit.test_app import _BrokenStore  # pyright: ignore[reportPrivateUsage]
from ticketscope.contract.search import OutcomeStatus, SearchResponse
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.http import page
from ticketscope.http.app import create_app
from ticketscope.settings import Settings

OUTCOMES = set(typing.get_args(OutcomeStatus))
FORM = {"content-type": "application/x-www-form-urlencoded"}


@dataclass
class Row:
    rank: int
    outcome_attr: str
    href: str | None = None
    title: str = ""
    kind: str = ""
    outcome: str = ""
    summary: str | None = None


@dataclass
class Parsed:
    rows: list[Row] = field(default_factory=list[Row])
    textarea: str | None = None
    form: dict[str, str] | None = None
    messages: list[str] = field(default_factory=list[str])


class _PageParser(HTMLParser):
    """Reads the result rows, the form and the textarea with stdlib `html.parser`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out = Parsed()
        self._capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        css = a.get("class", "").split()
        if tag == "form":
            self.out.form = a
        elif tag == "textarea" and a.get("name") == "q":
            self.out.textarea = ""
            self._capture = "textarea"
        elif tag == "li" and "result" in css:
            self.out.rows.append(Row(rank=int(a["data-rank"]), outcome_attr=a["data-outcome"]))
        elif self.out.rows and "title" in css:
            self.out.rows[-1].href = a.get("href")
            self._capture = "title"
        elif self.out.rows and "kind" in css:
            self._capture = "kind"
        elif self.out.rows and "outcome" in css:
            self._capture = "outcome"
        elif self.out.rows and "summary" in css:
            self.out.rows[-1].summary = ""
            self._capture = "summary"
        elif "message" in css:
            self.out.messages.append("")
            self._capture = "message"

    def handle_endtag(self, tag: str) -> None:
        self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture == "textarea":
            self.out.textarea = (self.out.textarea or "") + data
        elif self._capture == "message":
            self.out.messages[-1] += data
        elif self._capture is not None:
            row = self.out.rows[-1]
            setattr(row, self._capture, (getattr(row, self._capture) or "") + data)


def parse(html: str) -> Parsed:
    parser = _PageParser()
    parser.feed(html)
    parser.close()
    # Browsers drop one newline right after <textarea> (HTML spec); html.parser does not.
    if parser.out.textarea is not None and parser.out.textarea.startswith("\n"):
        parser.out.textarea = parser.out.textarea[1:]
    return parser.out


def _html(response: httpx2.Response, status: int = 200) -> Parsed:
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    return parse(response.text)


@pytest.fixture
def client(fixture_store: InMemoryCorpusStore) -> TestClient:
    return TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))


def _post(client: TestClient, query: str) -> httpx2.Response:
    return client.post("/", content=urlencode({"q": query}), headers=FORM)


def test_open_page_is_the_form_with_no_results(client: TestClient) -> None:
    body = _html(client.get("/"))
    assert body.form is not None
    assert body.form.get("method") == "post"
    assert body.form.get("action") == "/"
    assert body.textarea == ""
    assert body.rows == []
    assert "<title>ticketscope</title>" in client.get("/").text


def test_results_match_v1_search(client: TestClient) -> None:
    response = _post(client, TARGET_QUERY)
    body = _html(response)
    assert body.textarea == TARGET_QUERY
    assert "<ol" in response.text
    assert body.rows
    assert [r.rank for r in body.rows] == list(range(1, len(body.rows) + 1))
    api = SearchResponse.model_validate(
        client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "keyword"}).json()
    )
    assert len(body.rows) == len(api.results)
    for row, result in zip(body.rows, api.results, strict=True):
        assert row.href == result.issue.url
        assert row.title == result.issue.title
        assert row.kind == {"short": "short", "log_heavy": "log-heavy"}[result.issue.kind]
        assert row.outcome_attr in OUTCOMES
        assert row.outcome_attr == row.outcome == result.outcome.status
        assert row.summary == result.outcome.summary
    assert api.results[0].issue.number == TARGET_NUMBER
    assert body.rows[0].outcome_attr == "fixed"


def test_v1_search_still_answers_json(client: TestClient) -> None:
    _post(client, TARGET_QUERY)
    response = client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "keyword"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["results"][0]["issue"]["number"] == TARGET_NUMBER


def test_get_link_gives_the_same_rows_as_post(client: TestClient) -> None:
    by_get = _html(client.get("/", params={"q": TARGET_QUERY}))
    by_post = _html(_post(client, TARGET_QUERY))
    assert by_get.rows
    assert by_get.rows == by_post.rows
    assert by_get.textarea == TARGET_QUERY


@pytest.mark.parametrize("query", ["", "   \n\t  "], ids=["empty", "whitespace"])
def test_blank_query_prompts_and_does_not_search(query: str) -> None:
    # _BrokenStore raises on any call: a 200 proves no search (nor version check) ran.
    client = TestClient(create_app(store=_BrokenStore(), settings=Settings()))
    body = _html(_post(client, query))
    assert body.rows == []
    assert body.messages == [page.BLANK_MESSAGE]
    assert body.form is not None


def test_no_match_is_the_empty_state(client: TestClient) -> None:
    body = _html(_post(client, NO_MATCH_QUERY))
    assert body.rows == []
    assert body.messages == [page.NO_MATCH_MESSAGE]
    assert "No matching issues" in body.messages[0]


@pytest.mark.parametrize("method", ["get", "post"])
def test_corpus_not_loaded_is_a_503_page(method: str) -> None:
    client = TestClient(create_app(store=InMemoryCorpusStore(), settings=Settings()))
    response = (
        client.get("/", params={"q": TARGET_QUERY})
        if method == "get"
        else _post(client, TARGET_QUERY)
    )
    body = _html(response, 503)
    assert body.rows == []
    assert body.messages == [page.NOT_LOADED_MESSAGE]
    assert "not loaded" in body.messages[0]
    assert "Traceback" not in response.text


@pytest.mark.parametrize("method", ["get", "post"])
def test_store_failure_is_a_generic_500_page(method: str, caplog: pytest.LogCaptureFixture) -> None:
    client = TestClient(
        create_app(store=_BrokenStore(), settings=Settings()), raise_server_exceptions=False
    )
    with caplog.at_level(logging.ERROR, logger="ticketscope.http.app"):
        response = (
            client.get("/", params={"q": TARGET_QUERY})
            if method == "get"
            else _post(client, TARGET_QUERY)
        )
    body = _html(response, 500)
    assert body.messages == [page.ERROR_MESSAGE]
    assert "database down" not in response.text
    assert "Traceback" not in response.text
    assert any(r.exc_info for r in caplog.records), "exception not logged"


class _FailingSearchStore(InMemoryCorpusStore):
    """Loaded, but the search itself raises."""

    def keyword_search(self, query: str, k: int) -> list[typing.Any]:
        raise ConnectionError("database down")


def test_search_failure_after_version_check_is_a_500_page() -> None:
    client = TestClient(
        create_app(store=_FailingSearchStore(corpus_version="v"), settings=Settings()),
        raise_server_exceptions=False,
    )
    response = _post(client, TARGET_QUERY)
    _html(response, 500)
    assert "database down" not in response.text


def test_invalid_stored_row_is_a_500_page(caplog: pytest.LogCaptureFixture) -> None:
    # A row the contract rejects fails inside `_results`: still the HTML error state.
    issue = IssueRecord(
        number=1,
        title="t",
        url="https://example.test/1",
        kind="short",
        state="closed",
        outcome_status=typing.cast(typing.Any, "bogus"),
    )
    store = InMemoryCorpusStore(((issue, "quokka"),), corpus_version="v")
    client = TestClient(create_app(store=store, settings=Settings()), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="ticketscope.http.app"):
        response = _post(client, "quokka")
    body = _html(response, 500)
    assert body.messages == [page.ERROR_MESSAGE]
    assert body.rows == []
    assert "Traceback" not in response.text
    assert any(r.exc_info for r in caplog.records), "exception not logged"


def test_repeated_q_takes_the_last_value_on_get_and_post(client: TestClient) -> None:
    pairs = [("q", NO_MATCH_QUERY), ("q", TARGET_QUERY)]
    by_get = _html(client.get(f"/?{urlencode(pairs)}"))
    by_post = _html(client.post("/", content=urlencode(pairs), headers=FORM))
    assert by_get.textarea == by_post.textarea == TARGET_QUERY
    assert by_get.rows and by_get.rows == by_post.rows


def test_query_is_escaped(client: TestClient) -> None:
    query = "<script>alert(1)</script>"
    response = _post(client, query)
    body = _html(response)
    assert "<script" not in response.text
    assert "&lt;script&gt;" in response.text
    assert body.textarea == query


def test_stored_title_and_unsafe_url_are_escaped() -> None:
    issue = IssueRecord(
        number=1,
        title="<script>x</script>",
        url="javascript:alert(1)",
        kind="short",
        state="closed",
        outcome_status="duplicate",
        outcome_summary='"><script>y</script>',
        outcome_source="label",
        outcome_ref="javascript:alert(2)",
    )
    store = InMemoryCorpusStore(((issue, "quokka"),), corpus_version="v")
    client = TestClient(create_app(store=store, settings=Settings()))
    response = _post(client, "quokka")
    body = _html(response)
    assert "<script" not in response.text
    assert "&lt;script&gt;x&lt;/script&gt;" in response.text
    assert 'href="javascript' not in response.text
    assert [r.title for r in body.rows] == ["<script>x</script>"]
    assert body.rows[0].href is None
    assert body.rows[0].summary == '"><script>y</script>'


def test_a_pasted_log_of_4kb_ranks(client: TestClient) -> None:
    frame = "\tat net.minecraft.zephyrcache.Eviction.stall(Eviction.java:42)\n"
    query = "java.lang.IllegalStateException: node drain\n" + frame * 80
    assert len(query.encode()) >= 4096
    body = _html(_post(client, query))
    assert body.rows
    assert body.textarea == query


def test_footer_carries_the_corpus_attribution(client: TestClient) -> None:
    text = client.get("/").text
    assert "The Public Jira Dataset v7" in text
    assert "CC BY 4.0" in text
    assert "The text belongs to its authors" in text
    readme = (REPO / "README.md").read_text(encoding="utf-8").splitlines()[6]
    assert readme.startswith("Issue text from the Mojang bug tracker")
    assert html.escape(readme, quote=True) in text


def test_page_has_no_script_or_external_assets(client: TestClient) -> None:
    text = _post(client, TARGET_QUERY).text
    assert "<script" not in text
    assert "<link" not in text
    assert "src=" not in text


def test_page_module_imports_only_stdlib_contract_and_core() -> None:
    path = REPO / "src" / "ticketscope" / "http" / "page.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ] + [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and not node.level
    ]
    bad = [
        m
        for m in modules
        if m.split(".")[0] not in sys.stdlib_module_names
        and not m.startswith(("ticketscope.contract", "ticketscope.core"))
    ]
    assert not bad


def test_leading_newline_in_the_query_is_echoed(client: TestClient) -> None:
    query = "\n" + TARGET_QUERY
    body = _html(_post(client, query))
    assert body.textarea == query
