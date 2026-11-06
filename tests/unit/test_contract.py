import pytest
from pydantic import ValidationError

from ticketscope.contract.search import SearchRequest, SearchResponse


def test_mode_is_optional_with_no_default() -> None:
    request = SearchRequest.model_validate({"query": "q"})
    assert request.mode is None
    assert request.k == 10


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchRequest.model_validate({"query": "q", "mode": "nope"})


def test_query_is_required() -> None:
    with pytest.raises(ValidationError):
        SearchRequest.model_validate({"mode": "keyword"})


def test_unknown_fields_pass_through() -> None:
    request = SearchRequest.model_validate({"query": "q", "future": 1})
    assert request.model_dump()["future"] == 1


def test_response_has_the_v1_shape() -> None:
    body = {
        "mode": "keyword",
        "score_kind": "bm25",
        "corpus_version": "fixture",
        "results": [
            {
                "rank": 1,
                "score": 2.5,
                "issue": {
                    "number": 900003,
                    "title": "t",
                    "url": "https://example.invalid/900003",
                    "kind": "log_heavy",
                    "state": "closed",
                    "added_later": True,
                },
                "outcome": {"status": "unknown", "summary": None, "source": None, "ref": None},
            }
        ],
    }
    response = SearchResponse.model_validate(body)
    assert response.model_dump() == body


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("score_kind",), "tfidf"),
        (("results", 0, "issue", "kind"), "medium"),
        (("results", 0, "outcome", "status"), "won't fix"),
        (("results", 0, "outcome", "source"), "guess"),
    ],
)
def test_response_enums_are_closed(path: tuple[str | int, ...], value: str) -> None:
    body: dict[str, object] = {
        "mode": "keyword",
        "score_kind": "bm25",
        "corpus_version": "fixture",
        "results": [
            {
                "rank": 1,
                "score": 1.0,
                "issue": {
                    "number": 1,
                    "title": "t",
                    "url": "u",
                    "kind": "short",
                    "state": "closed",
                },
                "outcome": {"status": "unknown", "summary": None, "source": None, "ref": None},
            }
        ],
    }
    target: object = body
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError):
        SearchResponse.model_validate(body)
