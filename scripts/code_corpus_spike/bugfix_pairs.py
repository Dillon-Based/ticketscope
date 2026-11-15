"""Print the pre-release / rc / patch pairs (old:new) that have fixed MC issues, or the
distinct version ids they need.

usage: bugfix_pairs.py <manifest.json> <mc_fixed.jsonl> pairs|ids
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

man = json.loads(Path(sys.argv[1]).read_text())["versions"]
ids = [v["id"] for v in man]
low = {i.lower(): k for k, i in enumerate(ids)}


def mid(name: str) -> str:
    n = re.sub(r"^Minecraft\s+", "", name.strip(), flags=re.IGNORECASE)
    m = re.match(r"^(\S+)\s+Pre-?release\s*(\d+)$", n, flags=re.IGNORECASE)
    if m:
        return f"{m.group(1)}-pre{m.group(2)}"
    m = re.match(r"^(\S+)\s+Release Candidate\s*(\d+)$", n, flags=re.IGNORECASE)
    return f"{m.group(1)}-rc{m.group(2)}" if m else n


count: Counter[int] = Counter()
for line in Path(sys.argv[2]).read_text().splitlines():
    k = low.get(mid(json.loads(line)["fix"]).lower())
    if k is not None and man[k]["releaseTime"] >= "2019-09-04":
        count[k] += 1
pairs = [
    (ids[k + 1], ids[k])
    for k in sorted(count, reverse=True)
    if re.search(r"-pre|-rc|^\d+\.\d+(\.\d+)?$", ids[k])
]
if sys.argv[3] == "pairs":
    print(" ".join(f"{a}:{b}" for a, b in pairs))
else:
    print(" ".join(dict.fromkeys(x for p in pairs for x in p)))
