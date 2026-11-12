"""Tempo lookups shared by `tests/smoke` and `tests/mcp` (one copy since story 4.6, R-008)."""

import base64
import json
import os
import subprocess
import urllib.parse
from typing import Any

PLATFORM_NAMESPACE = os.environ.get("TICKETSCOPE_PLATFORM_NAMESPACE", "platform")
_PROXY = f"/api/v1/namespaces/{PLATFORM_NAMESPACE}/services/tempo:3200/proxy"
_KINDS = {"1": "INTERNAL", "2": "SERVER", "3": "CLIENT"}


def attributes(item: dict[str, Any]) -> dict[str, Any]:
    """OTLP JSON attributes as a plain dict (`intValue` arrives as a string)."""
    out: dict[str, Any] = {}
    for attribute in item.get("attributes") or []:
        value: dict[str, Any] = attribute.get("value") or {}
        if "intValue" in value:
            out[attribute["key"]] = int(value["intValue"])
        elif value:
            out[attribute["key"]] = next(iter(value.values()))
    return out


def spans(trace: dict[str, Any]) -> list[dict[str, Any]]:
    """Every span of a Tempo `/api/v2/traces` body, with its resource's `service.name`
    (`service`), its attributes (`attrs`) and its ids as hex (`id`, `parent`, `trace`)."""
    body: dict[str, Any] = trace.get("trace", trace)
    found: list[dict[str, Any]] = []
    for resource_spans in body.get("resourceSpans") or []:
        service = attributes(resource_spans.get("resource") or {}).get("service.name")
        for scope_spans in resource_spans.get("scopeSpans") or []:
            for span in scope_spans.get("spans") or []:
                found.append(
                    {
                        **span,
                        "service": service,
                        "attrs": attributes(span),
                        "id": hex_id(span.get("spanId", "")),
                        "parent": hex_id(span.get("parentSpanId", "")),
                        "trace": hex_id(span.get("traceId", "")),
                    }
                )
    return found


def hex_id(value: str) -> str:
    """A span or trace id as lowercase hex, whether Tempo sent hex or base64.

    Hex ids are 16 (span) or 32 (trace) characters; base64 of 8 or 16 bytes is 12 or 24."""
    if len(value) in (16, 32) and all(c in "0123456789abcdefABCDEF" for c in value):
        return value.lower()
    return base64.b64decode(value).hex() if value else ""


def kind(span: dict[str, Any]) -> str:
    """`SPAN_KIND_SERVER` or a bare enum number, as `SERVER`."""
    raw = str(span.get("kind", ""))
    return _KINDS.get(raw, raw.removeprefix("SPAN_KIND_"))


def _get(path: str) -> tuple[int, str]:
    result = subprocess.run(
        ["kubectl", "get", "--raw", f"{_PROXY}{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return 200, result.stdout
    return 404 if "NotFound" in result.stderr else 0, result.stdout + result.stderr


def trace_by_id(trace_id: str) -> tuple[int, str]:
    """Tempo's trace-by-id through the API server's service proxy (Tempo is not exposed)."""
    return _get(f"/api/v2/traces/{trace_id}")


def search(traceql: str, start: int, end: int, since_ns: int = 0) -> list[str]:
    """Trace ids that match `traceql` within [start, end] (unix seconds) and began at or
    after `since_ns` (unix nanoseconds), so a trace a moment before the call is not counted."""
    query = urllib.parse.urlencode({"q": traceql, "start": start, "end": end, "limit": 200})
    status, body = _get(f"/api/search?{query}")
    if status != 200:
        return []
    try:
        found = json.loads(body).get("traces") or []
    except ValueError:
        return []
    return [
        str(trace["traceID"])
        for trace in found
        if int(trace.get("startTimeUnixNano") or 0) >= since_ns
    ]
