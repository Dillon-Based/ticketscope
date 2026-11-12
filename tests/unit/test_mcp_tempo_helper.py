"""The shared Tempo helper (`tests/tempo.py`) on recorded-shape bodies (R-008): base64 and hex
span ids, string `intValue`s, numeric and named span kinds."""

import base64
from typing import Any

from tests import tempo

SPAN_ID = "00f067aa0ba902b7"
PARENT_ID = "b7ad6b7169203331"
TRACE_ID = "0af7651916cd43dd8448eb211c80319c"


def _b64(value: str) -> str:
    return base64.b64encode(bytes.fromhex(value)).decode()


def _body(span_id: str, parent: str, trace_id: str, kind: Any) -> dict[str, Any]:
    return {
        "trace": {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "ticketscope-mcp"}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": trace_id,
                                    "spanId": span_id,
                                    "parentSpanId": parent,
                                    "name": "tools/call search_similar_issues",
                                    "kind": kind,
                                    "attributes": [
                                        {"key": "server.port", "value": {"intValue": "8000"}},
                                        {"key": "k", "value": {"stringValue": "v"}},
                                        {"key": "ok", "value": {"boolValue": True}},
                                    ],
                                }
                            ]
                        }
                    ],
                }
            ]
        }
    }


def test_hex_and_base64_ids_parse_to_the_same_span() -> None:
    hexed = tempo.spans(_body(SPAN_ID, PARENT_ID, TRACE_ID, "SPAN_KIND_SERVER"))
    encoded = tempo.spans(_body(_b64(SPAN_ID), _b64(PARENT_ID), _b64(TRACE_ID), "SPAN_KIND_SERVER"))
    for [span] in (hexed, encoded):
        assert (span["id"], span["parent"], span["trace"]) == (SPAN_ID, PARENT_ID, TRACE_ID)
        assert span["service"] == "ticketscope-mcp"


def test_int_value_strings_become_ints() -> None:
    [span] = tempo.spans(_body(SPAN_ID, PARENT_ID, TRACE_ID, 2))
    assert span["attrs"] == {"server.port": 8000, "k": "v", "ok": True}


def test_kinds_by_name_and_number() -> None:
    assert tempo.kind({"kind": "SPAN_KIND_CLIENT"}) == "CLIENT"
    assert tempo.kind({"kind": 2}) == "SERVER"
    assert tempo.kind({"kind": "1"}) == "INTERNAL"


def test_a_missing_parent_is_empty() -> None:
    [span] = tempo.spans(_body(SPAN_ID, "", TRACE_ID, 2))
    assert span["parent"] == ""
