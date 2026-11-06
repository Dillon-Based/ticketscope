"""Render findings.md's tables from the spike CSVs.

    python3 tables.py <csv> instances|projects|subsets

Bold rows meet the pair test: at least 1,000 pairs and at least 200 of each kind.
"""

import csv
import sys

OUTCOMES = ("duplicate", "fixed", "not_planned", "stale", "answered")
HYGIENE = ("wiki", "mention", "email", "secret", "nul")
HEADER = [
    "Resolved issues",
    "Log-heavy",
    "Pairs",
    "Pairs short",
    "Pairs log-heavy",
    "Target open / outside / no link",
    "Dup / fixed / not_planned / stale / answered",
    "Unknown",
    "Bug",
    "Question/Support",
    "Wiki / mention / email / secret / NUL",
]


def pct(x: str) -> str:
    return f"{float(x) * 100:.1f}%"


def n(r: dict[str, str], key: str) -> str:
    return f"{int(r[key]):,}"


def meets(r: dict[str, str]) -> bool:
    return (
        int(r["pairs"]) >= 1000
        and int(r["pairs_short"]) >= 200
        and int(r["pairs_log_heavy"]) >= 200
    )


def label(r: dict[str, str], mode: str) -> str:
    if mode == "instances":
        return r["instance"]
    return (
        f"{r['instance']} {r['project']}"
        if mode == "projects"
        else (f"{r['project']} ({r['instance']})")
    )


def main() -> None:
    path, mode = sys.argv[1], sys.argv[2]
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if mode == "projects":
        rows = [r for r in rows if int(r["issues_resolved"]) >= 5000 and int(r["pairs"]) >= 300]
        rows.sort(key=lambda r: -int(r["pairs_log_heavy"]))
    name = {"instances": "Instance", "projects": "Project", "subsets": "Subset"}[mode]
    print("| " + " | ".join([name, *HEADER]) + " |")
    print("|" + "---|" * (len(HEADER) + 1))
    for r in rows:
        text = label(r, mode)
        targets = " / ".join(
            n(r, k) for k in ("pairs_target_open", "pairs_out_of_scope", "dup_no_target")
        )
        cells = [
            f"**{text}**" if meets(r) else text,
            n(r, "issues_resolved"),
            n(r, "log_heavy"),
            n(r, "pairs"),
            n(r, "pairs_short"),
            n(r, "pairs_log_heavy"),
            targets,
            " / ".join(pct(r[f"share_{o}"]) for o in OUTCOMES),
            pct(r["share_unknown"]),
            pct(r["type_bug"]),
            pct(r["type_question_support"]),
            " / ".join(n(r, f"hyg_{h}") for h in HYGIENE),
        ]
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
