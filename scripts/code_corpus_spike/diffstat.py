"""Compare two decompiled versions: which files changed, and by how many lines.

usage: diffstat.py <old src dir> <new src dir> [<out json>]
"""

import difflib
import json
import sys
from collections import Counter
from pathlib import Path

old, new = Path(sys.argv[1]), Path(sys.argv[2])


def files(root: Path) -> dict[str, Path]:
    return {str(p.relative_to(root)): p for p in root.rglob("*") if p.is_file()}


def group(rel: str) -> str:
    if rel.endswith(".java"):
        return "java"
    top = rel.split("/", 1)[0]
    return top if top in ("assets", "data") else "other"


a, b = files(old), files(new)
stats: dict[str, Counter[str]] = {g: Counter() for g in ("java", "data", "assets", "other")}
changed: dict[str, dict[str, int]] = {}
for rel in sorted(a.keys() | b.keys()):
    g = stats[group(rel)]
    if rel not in a:
        g["added"] += 1
        changed[rel] = {"added_file": 1}
        continue
    if rel not in b:
        g["removed"] += 1
        changed[rel] = {"removed_file": 1}
        continue
    g["common"] += 1
    da, db = a[rel].read_bytes(), b[rel].read_bytes()
    if da == db:
        continue
    g["modified"] += 1
    if group(rel) == "java":
        la = da.decode(errors="replace").splitlines()
        lb = db.decode(errors="replace").splitlines()
        plus = minus = 0
        for line in difflib.unified_diff(la, lb, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                plus += 1
            elif line.startswith("-") and not line.startswith("---"):
                minus += 1
        g["lines_added"] += plus
        g["lines_removed"] += minus
        changed[rel] = {"plus": plus, "minus": minus}
    else:
        changed[rel] = {"modified": 1}

print(json.dumps({k: dict(v) for k, v in stats.items()}, indent=1))
java = sorted(
    ((v["plus"] + v["minus"], k) for k, v in changed.items() if "plus" in v), reverse=True
)
sizes = [n for n, _ in java]
if sizes:
    print("java modified files:", len(sizes), "median changed lines:", sizes[len(sizes) // 2])
    print("files with <=4 changed lines:", sum(1 for n in sizes if n <= 4))
    print("top 15:", [(n, k.rsplit("/", 1)[-1]) for n, k in java[:15]])
if len(sys.argv) > 3:
    Path(sys.argv[3]).write_text(json.dumps(changed))
