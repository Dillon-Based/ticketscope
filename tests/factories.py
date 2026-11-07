"""Raw test inputs; response expectations stay independent of these builders."""


def search_payload(query: str, **overrides: object) -> dict[str, object]:
    """Leave optional fields absent unless the scenario explicitly supplies them."""
    return {"query": query, **overrides}


def form_payload(query: str) -> dict[str, str]:
    return {"q": query}


def outcome_payload(**overrides: object) -> dict[str, object]:
    return {"status": "unknown", "summary": None, "source": None, "ref": None, **overrides}


def issue_outcome_payload(number: int, **outcome: object) -> dict[str, object]:
    return {"issue": {"number": number}, "outcome": outcome_payload(**outcome)}
