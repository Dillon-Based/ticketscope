import pytest
from pydantic import ValidationError

from tests.factories import issue_payload, outcome_payload, search_payload
from ticketscope.contract.search import IssueResponse, SearchRequest, SearchResponse


def test_mode_is_optional_with_no_default() -> None:
    request = SearchRequest.model_validate(search_payload("q"))
    assert request.mode is None
    assert request.k == 10


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchRequest.model_validate(search_payload("q", mode="nope"))


def test_query_is_required() -> None:
    with pytest.raises(ValidationError):
        SearchRequest.model_validate({"mode": "keyword"})


def test_unknown_fields_pass_through() -> None:
    request = SearchRequest.model_validate(search_payload("q", future=1))
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
                "issue": issue_payload(
                    900003,
                    url="https://example.invalid/900003",
                    kind="log_heavy",
                    added_later=True,
                ),
                "outcome": outcome_payload(),
            }
        ],
    }
    response = SearchResponse.model_validate(body)
    # `key` is the one optional field the contract adds (C-8): absent in, null out.
    assert response.model_dump() == {
        **body,
        "results": [{**body["results"][0], "issue": {**body["results"][0]["issue"], "key": None}}],
    }


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
                "issue": issue_payload(),
                "outcome": outcome_payload(),
            }
        ],
    }
    target: object = body
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError):
        SearchResponse.model_validate(body)


@pytest.mark.parametrize("k", [1, 50])
def test_k_edges_are_accepted(k: int) -> None:
    assert SearchRequest.model_validate(search_payload("q", k=k)).k == k


@pytest.mark.parametrize("k", [0, 51, -1])
def test_k_outside_1_to_50_is_rejected(k: int) -> None:
    with pytest.raises(ValidationError):
        SearchRequest.model_validate(search_payload("q", k=k))


def test_issue_response_round_trips_an_unknown_field() -> None:
    body = {
        "issue": issue_payload(
            900003,
            url="https://bugs.mojang.com/browse/MCD-9003",
            kind="log_heavy",
            body="a body",
            key="MCD-9003",
        ),
        "outcome": outcome_payload(status="fixed", summary="Fixed"),
        "added_later": [1, 2],
    }
    assert IssueResponse.model_validate(body).model_dump() == body


def test_issue_response_body_may_be_null_but_not_missing() -> None:
    body: dict[str, object] = {
        "issue": issue_payload(state="open"),
        "outcome": outcome_payload(),
    }
    with pytest.raises(ValidationError):
        IssueResponse.model_validate(body)
    body["issue"]["body"] = None  # type: ignore[index]
    assert IssueResponse.model_validate(body).issue.body is None
