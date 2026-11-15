"""Does a live model, given the two code tools, name a file the fix changed?

For each sampled ticket a headless Claude Code run gets the ticket text and only the
prototype's MCP tools (`search_code`, `get_code`) over the code as it was before the fix. It
answers with up to three file paths. A path is right when the fix version changed that file.
The same tickets are scored with the ranking alone (the top three of `search_code` on the
ticket text), so the two can be compared.

    llm_agent_check.py prepare <mc_fixed.jsonl> <mc root> <work dir> <per pair> <old>:<new>...
    llm_agent_check.py run <work dir> <ticket key> [<model>]
    llm_agent_check.py score <work dir>

`prepare` keeps the pairs whose fix changed 11 to 40 Java files and builds an index per pair.
The work dir holds source text and ticket text: keep it outside the repository.
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import code_index
from keyword_check import manifest_id

HERE = Path(__file__).parent
PROMPT = """A bug was reported against a Java game. Find the source files that most likely \
need to change to fix it.

You have two tools: search_code finds files by keyword, get_code reads a file. Search with \
your own words as well as the ticket's, read the code you find, and search again when the \
results do not fit. Use at most about 10 tool calls.

Finish with exactly one line of JSON and nothing after it:
{{"files": ["<path>", "<path>", "<path>"]}}
Give up to 3 paths, exactly as search_code returned them, most likely first.

Ticket title: {summary}

Ticket text:
{description}
"""
SYSTEM = "You are helping a support engineer find where in a codebase a reported bug lives."


def prepare(args: list[str]) -> None:
    issues_path, root, work, per_pair = Path(args[0]), Path(args[1]), Path(args[2]), int(args[3])
    by_fix: dict[str, list[dict]] = {}
    for line in issues_path.read_text().splitlines():
        issue = json.loads(line)
        by_fix.setdefault(manifest_id(issue["fix"]).lower(), []).append(issue)
    (work / "index").mkdir(parents=True, exist_ok=True)
    tickets = []
    for pair in args[4:]:
        old, new = pair.split(":")
        diff = json.loads((root / f"diff-{old}-{new}.json").read_text())
        relevant = sorted(
            k for k, v in diff.items() if k.endswith(".java") and "added_file" not in v
        )
        if not 11 <= len(relevant) <= 40:
            continue
        index = work / "index" / f"{old}.sqlite"
        if not index.exists():
            code_index.build(root / old / "src", index)
        for issue in sorted(by_fix.get(new.lower(), []), key=lambda i: i["key"])[:per_pair]:
            tickets.append({**issue, "old": old, "new": new, "relevant": relevant})
    (work / "tickets.json").write_text(json.dumps(tickets))
    print(f"{len(tickets)} tickets from {len({t['old'] for t in tickets})} pairs")


def run(args: list[str]) -> None:
    work, key = Path(args[0]), args[1]
    model = args[2] if len(args) > 2 else "sonnet"
    ticket = next(t for t in json.loads((work / "tickets.json").read_text()) if t["key"] == key)
    out = work / "runs" / f"{key}.json"
    if out.exists():
        return
    out.parent.mkdir(exist_ok=True)
    config = work / "runs" / f"{key}.mcp.json"
    config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "code": {
                        "command": sys.executable,
                        "args": [str(HERE / "mcp_code_server.py")],
                        "env": {
                            "TICKETSCOPE_CODE_INDEX": str(
                                work / "index" / f"{ticket['old']}.sqlite"
                            )
                        },
                    }
                }
            }
        )
    )
    empty = work / "cwd"
    empty.mkdir(exist_ok=True)
    prompt = PROMPT.format(summary=ticket["summary"], description=ticket["description"][:4000])
    done = subprocess.run(
        [
            "claude", "-p", prompt,
            "--model", model,
            "--system-prompt", SYSTEM,
            "--strict-mcp-config", "--mcp-config", str(config),
            "--tools", "",
            "--allowedTools", "mcp__code__search_code", "mcp__code__get_code",
            "--output-format", "json",
            "--no-session-persistence",
        ],
        cwd=empty, capture_output=True, text=True, timeout=420, check=False,
    )  # fmt: skip
    out.write_text(done.stdout or json.dumps({"is_error": True, "result": done.stderr[-2000:]}))


def _answer(text: str) -> list[str]:
    for line in reversed(text.strip().splitlines()):
        start = line.find("{")
        if start >= 0:
            try:
                files = json.loads(line[start : line.rfind("}") + 1]).get("files")
            except ValueError:
                continue
            if isinstance(files, list):
                return [f for f in files if isinstance(f, str)][:3]
    return []


def score(args: list[str]) -> None:
    work = Path(args[0])
    tickets = json.loads((work / "tickets.json").read_text())
    rows = []
    for ticket in tickets:
        path = work / "runs" / f"{ticket['key']}.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text())
        relevant = set(ticket["relevant"])
        picked = _answer(str(result.get("result", "")))
        db = sqlite3.connect(work / "index" / f"{ticket['old']}.sqlite")
        query = ticket["summary"] + "\n" + ticket["description"]
        ranked = [h.path for h in code_index.search(db, query, 10, "file")]
        db.close()
        rows.append(
            {
                "key": ticket["key"],
                "summary": ticket["summary"][:70],
                "answered": bool(picked),
                "llm@1": bool(picked[:1]) and picked[0] in relevant,
                "llm@3": any(p in relevant for p in picked),
                "rank@1": ranked[0] in relevant if ranked else False,
                "rank@3": any(p in relevant for p in ranked[:3]),
                "rank@10": any(p in relevant for p in ranked),
                "turns": result.get("num_turns", 0),
                "cost": result.get("total_cost_usd", 0.0),
                "picked": [p.rsplit("/", 1)[-1] for p in picked],
            }
        )
    n = len(rows)
    if not n:
        sys.exit("no runs yet")
    for row in rows:
        mark = "1st" if row["llm@1"] else "top3" if row["llm@3"] else "miss"
        base = (
            "1st"
            if row["rank@1"]
            else "top3"
            if row["rank@3"]
            else "top10"
            if row["rank@10"]
            else "miss"
        )
        print(
            f"{row['key']:<10} llm={mark:<4} ranking={base:<5} {row['summary']} -> {row['picked']}"
        )
    print()
    for name in ("answered", "llm@1", "llm@3", "rank@1", "rank@3", "rank@10"):
        print(f"{name}: {sum(r[name] for r in rows)}/{n} = {sum(r[name] for r in rows) / n:.2f}")
    turns, cost = sum(r["turns"] for r in rows), sum(r["cost"] for r in rows)
    print(f"mean turns {turns / n:.1f}, total cost ${cost:.2f}")
    (work / "scores.json").write_text(json.dumps(rows))


if __name__ == "__main__":
    {"prepare": prepare, "run": run, "score": score}[sys.argv[1]](sys.argv[2:])
