#!/usr/bin/env python3
"""Compare the deploy role's live inline policy with the one the bootstrap template renders.

    python3 scripts/bootstrap_drift.py \
        --template infra/bootstrap/policies/deploy-permissions.json.tftpl \
        --account-id <id> --region us-east-1 --bucket ticketscope-<id> \
        --zone-id <zone id> --hostname <hostname> --live live.json

`scripts/bootstrap-drift.sh` fetches `live.json` (the `PolicyDocument` of `aws iam
get-role-policy`) and calls this. Statements are matched by `Sid`; actions and resources compare
as sets. Exit 0: the role matches the template. Exit 1: drift, printed per statement, meaning
bootstrap has not been re-applied since the template changed. Exit 2: unreadable input.
Account ids are printed as <acct>, because the output goes into public logs.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ACCOUNT = re.compile(r"\b\d{12}\b")
PLACEHOLDER = re.compile(r"\$\{(\w+)\}")


def render(template: str, values: dict[str, str]) -> dict[str, Any]:
    """Render a `templatefile` that uses only `${name}` interpolation (no directives)."""
    if "%{" in template:
        raise ValueError("template uses directives; this renderer handles ${name} only")

    def sub(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise ValueError(f"template variable ${{{name}}} has no value")
        return values[name]

    return json.loads(PLACEHOLDER.sub(sub, template))


def _as_set(value: Any) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset([value])
    return frozenset(value)


def _statements(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i, stmt in enumerate(policy["Statement"]):
        sid = stmt.get("Sid") or f"<statement {i}>"
        out[sid] = stmt
    return out


def compare(expected: dict[str, Any], live: dict[str, Any]) -> list[str]:
    """Lines describing every difference; empty when the policies match."""
    want, have = _statements(expected), _statements(live)
    lines: list[str] = []
    for sid in sorted(want.keys() - have.keys()):
        lines.append(f"{sid}: in the template, missing from the role")
    for sid in sorted(have.keys() - want.keys()):
        lines.append(f"{sid}: on the role, not in the template")
    for sid in sorted(want.keys() & have.keys()):
        w, h = want[sid], have[sid]
        if w.get("Effect") != h.get("Effect"):
            lines.append(
                f"{sid}: Effect {h.get('Effect')} on the role, {w.get('Effect')} in the template"
            )
        for key in ("Action", "NotAction", "Resource", "NotResource"):
            ws, hs = _as_set(w.get(key)), _as_set(h.get(key))
            for item in sorted(ws - hs):
                lines.append(f"{sid}: {key} {item} missing from the role")
            for item in sorted(hs - ws):
                lines.append(f"{sid}: {key} {item} on the role, not in the template")
        if w.get("Condition") != h.get("Condition"):
            lines.append(f"{sid}: Condition differs")
    return [ACCOUNT.sub("<acct>", line) for line in lines]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--zone-id", required=True)
    parser.add_argument("--hostname", required=True)
    parser.add_argument(
        "--live", type=Path, required=True, help="the role's PolicyDocument as JSON"
    )
    args = parser.parse_args(argv)
    try:
        expected = render(
            args.template.read_text(encoding="utf-8"),
            {
                "account_id": args.account_id,
                "region": args.region,
                "bucket": args.bucket,
                "zone_id": args.zone_id,
                "hostname": args.hostname.rstrip(".").lower(),
            },
        )
        live = json.loads(args.live.read_text(encoding="utf-8"))
        lines = compare(expected, live)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"bootstrap-drift: cannot compare: {exc}", file=sys.stderr)
        return 2
    if not lines:
        print("bootstrap-drift: the deploy role matches the template")
        return 0
    print("bootstrap-drift: the deploy role differs from the template; re-apply bootstrap")
    print("(docs/runbooks/env-up.md, 'Widen the deploy role') before dispatching:")
    for line in lines:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
