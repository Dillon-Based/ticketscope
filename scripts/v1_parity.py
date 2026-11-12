#!/usr/bin/env python3
"""Capture and compare `POST /v1/search` responses across two deployed revisions.

    python3 scripts/v1_parity.py capture --url <gateway url> --host <gateway host> --out a.json
    python3 scripts/v1_parity.py compare [--drop-issue-key] a.json b.json

`capture` posts one keyword request per query in eval/golden-queries.json, plus one
plain query, and saves each request with its status and exact body. `compare` exits 0
only when every request's status and body are byte-identical in both files. Stories 6,
7 and 10 (AC-3 each) state this as "the same request after the change returns an
identical body". `--drop-issue-key` removes exactly `issue.key` from every result before
comparing, for a capture taken before story 4.4 added the field. Standard library only, so
any revision's checkout can run it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAIN_QUERY = "launcher crash"


def requests() -> list[dict[str, object]]:
    golden = json.loads((ROOT / "eval" / "golden-queries.json").read_text(encoding="utf-8"))
    queries = [(q["id"], q["query"]) for q in golden["queries"]] + [("plain", PLAIN_QUERY)]
    mode, k = golden.get("mode", "keyword"), golden.get("k", 10)
    return [{"id": qid, "body": {"query": text, "mode": mode, "k": k}} for qid, text in queries]


def post(url: str, host: str, body: dict[str, object]) -> tuple[int, str]:
    request = urllib.request.Request(
        f"{url.rstrip('/')}/v1/search",
        data=json.dumps(body).encode(),
        headers={"Host": host, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def capture(url: str, host: str, out: Path, label: str) -> int:
    saved = []
    for item in requests():
        status, text = post(url, host, item["body"])  # type: ignore[arg-type]
        saved.append({"id": item["id"], "request": item["body"], "status": status, "body": text})
    payload = {"label": label, "responses": saved}
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"captured {len(saved)} responses ({label}) -> {out}")
    return 0 if all(s["status"] == 200 for s in saved) else 1


def _without_issue_key(body: str) -> str:
    """The body with `issue.key` dropped from each result, and nothing else changed."""
    try:
        data = json.loads(body)
    except ValueError:
        return body
    if isinstance(data, dict):
        for result in data.get("results", []):
            if isinstance(result, dict) and isinstance(result.get("issue"), dict):
                result["issue"].pop("key", None)
    return json.dumps(data, sort_keys=True)


def compare(before: Path, after: Path, drop_issue_key: bool = False) -> int:
    a = json.loads(before.read_text(encoding="utf-8"))
    b = json.loads(after.read_text(encoding="utf-8"))
    rows_b = {r["id"]: r for r in b["responses"]}
    ok = True
    for row in a["responses"]:
        other = rows_b.get(row["id"])
        same = (
            other is not None
            and row["request"] == other["request"]
            and row["status"] == other["status"]
            and (
                _without_issue_key(row["body"]) == _without_issue_key(other["body"])
                if drop_issue_key
                else row["body"] == other["body"]
            )
        )
        hits = len(json.loads(row["body"]).get("results", [])) if row["status"] == 200 else 0
        verdict = "identical" if same else "DIFFERENT"
        print(f"{row['id']:<10} status {row['status']} results {hits:>2}  {verdict}")
        ok = ok and same and row["status"] == 200
    print(f"{a.get('label')} vs {b.get('label')}: {'IDENTICAL' if ok else 'DIFFERENT'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--url", required=True)
    cap.add_argument("--host", required=True)
    cap.add_argument("--out", type=Path, required=True)
    cap.add_argument("--label", default="")
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("before", type=Path)
    cmp_.add_argument("after", type=Path)
    cmp_.add_argument(
        "--drop-issue-key",
        action="store_true",
        help="drop exactly issue.key from each result before comparing",
    )
    args = parser.parse_args(argv)
    if args.command == "capture":
        return capture(args.url, args.host, args.out, args.label or str(args.out))
    return compare(args.before, args.after, args.drop_issue_key)


if __name__ == "__main__":
    sys.exit(main())
