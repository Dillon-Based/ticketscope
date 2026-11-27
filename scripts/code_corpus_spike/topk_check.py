"""Is a file the fix changed among the top k code results for a ticket?

The measure for an LLM consumer, which reads the top 10 to 20 results and can search again.
For each <old>:<new> pair the corpus is the Java files of <old>; a file is relevant when
<new> modified or removed it; the queries are the MC issues whose single fix version is <new>.
The control ranks the same corpus for issues fixed in versions at least a year away, and is
scored against the same relevant set. Pairs are grouped by how many files changed, because a
small change set is a precise label and a large one is not.

Two rankings from `code_index.py`: `file` ranks whole files; `method` ranks one chunk per
method, a file scoring as its best chunk.

usage: topk_check.py <mc_fixed.jsonl> <mc root> <manifest.json> <old>:<new>...
"""

import json
import math
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import code_index
from keyword_check import manifest_id

KS = (5, 10, 20)
CONTROL_SIZE = 60
YEAR = 365 * 86400


def release_times(manifest: Path) -> dict[str, float]:
    from datetime import datetime

    versions = json.loads(manifest.read_text())["versions"]
    return {v["id"].lower(): datetime.fromisoformat(v["releaseTime"]).timestamp() for v in versions}


def main() -> None:
    issues = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
    root = Path(sys.argv[2])
    when = release_times(Path(sys.argv[3]))
    by_fix: dict[str, list[dict]] = defaultdict(list)
    for issue in issues:
        by_fix[manifest_id(issue["fix"]).lower()].append(issue)
    mapped = sorted(
        (i for fix, group in by_fix.items() if when.get(fix, 0) >= 1567555200 for i in group),
        key=lambda i: i["key"],
    )
    tot: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for pair in sys.argv[4:]:
        old, new = pair.split(":")
        src = root / old / "src"
        diff_path = root / f"diff-{old}-{new}.json"
        if not diff_path.exists() or not src.exists():
            continue
        diff = json.loads(diff_path.read_text())
        relevant = {k for k, v in diff.items() if k.endswith(".java") and "added_file" not in v}
        real = by_fix.get(new.lower(), [])
        if not relevant or not real:
            continue
        index = root.parent / "index" / f"{old}.sqlite"
        index.parent.mkdir(exist_ok=True)
        n_docs, _ = code_index.build(src, index)
        db = sqlite3.connect(index)
        far = [
            i for i in mapped if abs(when[manifest_id(i["fix"]).lower()] - when[new.lower()]) > YEAR
        ]
        control = far[:: max(1, len(far) // CONTROL_SIZE)][:CONTROL_SIZE]
        n_rel = len(relevant)
        bucket = (
            "1-10"
            if n_rel <= 10
            else "11-40"
            if n_rel <= 40
            else "41-150"
            if n_rel <= 150
            else "151+"
        )
        for kind, queries in (("real", real), ("control", control)):
            row = tot[(bucket, kind)]
            row["pairs"] += 1
            row["rel"] += n_rel
            for k in KS:
                row[f"chance@{k}_x1e6"] += round(
                    1e6 * len(queries) * (1 - math.comb(n_docs - n_rel, k) / math.comb(n_docs, k))
                )
            for issue in queries:
                row["issues"] += 1
                query = issue["summary"] + "\n" + issue["description"]
                by_file = [h.path for h in code_index.search(db, query, max(KS), "file")]
                by_method = [h.path for h in code_index.search(db, query, max(KS), "method")]
                for k in KS:
                    row[f"file@{k}"] += any(rel in relevant for rel in by_file[:k])
                    row[f"method@{k}"] += any(rel in relevant for rel in by_method[:k])
        db.close()
        index.unlink()
        print(pair, bucket, n_rel, len(real), flush=True)
    if os.environ.get("TOPK_OUT"):  # raw counters, so runs over subsets of pairs can be summed
        raw = [{"bucket": b, "kind": k, **row} for (b, k), row in tot.items()]
        Path(os.environ["TOPK_OUT"]).write_text(json.dumps(raw))
    print()
    print(
        "changed files | queries | pairs | issues | "
        + " | ".join(f"file@{k} / method@{k} / chance@{k}" for k in KS)
    )
    for (bucket, kind), row in sorted(tot.items(), key=lambda kv: (len(kv[0][0]), kv[0])):
        n = row["issues"]
        cells = " | ".join(
            f"{row[f'file@{k}'] / n:.2f} / {row[f'method@{k}'] / n:.2f} / "
            f"{row[f'chance@{k}_x1e6'] / n / 1e6:.2f}"
            for k in KS
        )
        print(f"{bucket} | {kind} | {row['pairs']} | {n} | {cells}")


if __name__ == "__main__":
    main()
