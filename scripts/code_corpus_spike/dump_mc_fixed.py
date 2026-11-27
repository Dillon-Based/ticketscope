"""Write MC Fixed issues with exactly one fix version to a local jsonl (scratch only).

Reads the gunzipped mongodump archive on stdin. Keeps key, fix version, summary and
description; no reporter, assignee or comment data.
usage: dump_mc_fixed.py <worktree scripts dir> <out jsonl>
"""

import json
import sys

sys.path.insert(0, sys.argv[1])
from fixversion_coverage import collection_documents

n = 0
with open(sys.argv[2], "w") as out:
    for doc in collection_documents(sys.stdin.buffer, "Mojang"):
        f = doc.get("fields") or {}
        if (f.get("project") or {}).get("key") != "MC":
            continue
        if (f.get("resolution") or {}).get("name") != "Fixed":
            continue
        fix = [v["name"] for v in f.get("fixVersions") or [] if v.get("name")]
        if len(fix) != 1:
            continue
        out.write(
            json.dumps(
                {
                    "key": doc.get("key"),
                    "fix": fix[0],
                    "created": f.get("created"),
                    "summary": f.get("summary") or "",
                    "description": f.get("description") or "",
                }
            )
            + "\n"
        )
        n += 1
print("wrote", n)
