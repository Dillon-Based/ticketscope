"""Spike 1.12: convert a Jira subset into a schema-v1 snapshot for the timed load.

Spike evidence, not product code, and the output is not a publishable snapshot: it exists
so `scripts/time-load.sh` can time a load of the recommended subset. Keep the output out
of git (write it to a temporary directory).

    uv run --with pymongo python convert.py --subset Mojang:MC:2021-01-01:2022-01-01 \
        --out "$CLAUDE_JOB_DIR/tmp/snap" --version jira-mojang-mc-2021 [--with-open-targets]
    scripts/time-load.sh "$CLAUDE_JOB_DIR/tmp/snap" jira-mojang-mc-2021

Field mapping onto schema v1 (the gaps are findings for the replan):

- number: the Jira issue `id` (an integer, unique within one instance, not across them).
- url: `<jira_url>/browse/<key>`.
- title / body: `summary` / `description`, masked (ingest's `mask` plus `[~user]` mentions).
- state: `closed` when a resolution is set, else `open`. state_reason: `duplicate`,
  `not_planned` or `completed` from the proposed outcome mapping; null when open.
- labels: the Jira `labels`. comments: `author_association` is `NONE` for every comment,
  because Jira has no such field (the masked author id is left out: no identities).
- timeline: one `marked_as_duplicate` event, at the resolution time, for every
  duplicate-resolved issue with a Duplicate-mapped link (the "duplicates" direction, else
  the reversed-direction fallback of `measure.duplicate_target`), whether or not the target
  is in the snapshot. `source_url` is the target's browse URL; `source_number` is its issue
  id when it is in the snapshot, else null (an out-of-scope target).
- kinds sidecar: the extended kind rule over the description.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure import (
    SOURCES,
    SubsetSpec,
    comments_of,
    derive_outcome,
    duplicate_target,
    extended_kind,
    iter_issues,
    load_linktype_map,
    parse_time,
)

from ticketscope.core.snapshot import SnapshotIssue
from ticketscope.jobs.ingest.mask import mask

JIRA_USER_MARKER = "[~user]"
_JIRA_MENTION = re.compile(r"\[~(?:accountid:)?[^\]\n]+\]")


def mask_jira(text: str | None) -> str | None:
    if text is None:
        return None
    return _JIRA_MENTION.sub(JIRA_USER_MARKER, mask(text))


def _ts(moment: datetime | None) -> str | None:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ") if moment else None


def browse_url(base: str, key: str) -> str:
    return f"{base.rstrip('/')}/browse/{key}"


def to_snapshot(
    issue: dict[str, Any],
    base_url: str,
    linkmap: dict[str, str],
    ids: dict[str, int],
) -> dict[str, Any]:
    """One Jira issue as a schema-v1 line. `ids` maps the snapshot's keys to issue ids."""
    fields = issue.get("fields") or {}
    resolved = fields.get("resolution") is not None
    outcome, _ = derive_outcome(issue)
    closed_at = parse_time(fields.get("resolutiondate")) if resolved else None
    created_at = parse_time(fields.get("created"))
    if created_at is None:
        raise ValueError(f"{issue.get('key')}: no created time")
    if resolved and closed_at is None:
        closed_at = parse_time(fields.get("updated")) or created_at
    state_reason = None
    if resolved:
        state_reason = {"duplicate": "duplicate", "not_planned": "not_planned"}.get(
            outcome, "completed"
        )
    timeline = []
    if outcome == "duplicate":
        link = duplicate_target(issue, linkmap)
        if link is not None and link.target != issue["key"]:
            timeline.append(
                {
                    "event": "marked_as_duplicate",
                    "created_at": _ts(closed_at or created_at),
                    "source_number": ids.get(link.target),
                    "source_url": browse_url(base_url, link.target),
                    "source_is_pull_request": None,
                    "source_merged": None,
                }
            )
    comments = []
    for comment in comments_of(issue):
        created = parse_time(comment.get("created"))
        if created is None:
            continue
        comments.append(
            {
                "author_association": "NONE",
                "body": mask_jira(comment.get("body") or "") or "",
                "created_at": _ts(created),
            }
        )
    return {
        "number": int(issue["id"]),
        "url": browse_url(base_url, issue["key"]),
        "title": mask_jira(fields.get("summary") or "") or "",
        "body": mask_jira(fields.get("description")),
        "state": "closed" if resolved else "open",
        "state_reason": state_reason,
        "created_at": _ts(created_at),
        "closed_at": _ts(closed_at),
        "labels": [{"name": str(name)} for name in fields.get("labels") or []],
        "comments": comments,
        "timeline": timeline,
    }


def select(
    issues: list[dict[str, Any]], linkmap: dict[str, str], with_open_targets: bool
) -> list[dict[str, Any]]:
    """The resolved issues, plus (optionally) the unresolved targets of their duplicates.

    The first document wins when the dump holds an issue key more than once (as measure.py).
    """
    first: dict[str, dict[str, Any]] = {}
    for issue in issues:
        first.setdefault(issue["key"], issue)
    issues = list(first.values())
    resolved = [i for i in issues if (i.get("fields") or {}).get("resolution") is not None]
    if not with_open_targets:
        return resolved
    by_key = {i["key"]: i for i in issues}
    keep = {i["key"] for i in resolved}
    extra = []
    for issue in resolved:
        if derive_outcome(issue)[0] != "duplicate":
            continue
        link = duplicate_target(issue, linkmap)
        if link and link.target in by_key and link.target not in keep:
            keep.add(link.target)
            extra.append(by_key[link.target])
    return resolved + extra


def convert(
    spec: SubsetSpec, out_dir: Path, version: str, with_open_targets: bool
) -> dict[str, Any]:
    linkmap = load_linktype_map()
    base_url = json.loads(SOURCES.read_text(encoding="utf-8"))[spec.instance]["jira_url"]
    issues = [i for i in iter_issues(spec.instance, spec.query()) if spec.contains(i)]
    chosen = select(issues, linkmap, with_open_targets)
    ids = {i["key"]: int(i["id"]) for i in chosen}
    out_dir.mkdir(parents=True, exist_ok=True)
    kinds: dict[str, str] = {}
    with gzip.open(out_dir / f"{version}.jsonl.gz", "wt", encoding="utf-8") as out:
        for issue in chosen:
            line = to_snapshot(issue, base_url, linkmap, ids)
            SnapshotIssue.model_validate(line)  # fail here, not in the load
            out.write(json.dumps(line, ensure_ascii=False) + "\n")
            kinds[str(line["number"])] = extended_kind(line["body"])
    (out_dir / f"{version}-kinds.json").write_text(json.dumps(kinds, indent=0))
    report = {
        "version": version,
        "issues": len(chosen),
        "open_targets_added": len(chosen)
        - sum(1 for i in chosen if (i.get("fields") or {}).get("resolution") is not None),
        "short": sum(1 for k in kinds.values() if k == "short"),
        "log_heavy": sum(1 for k in kinds.values() if k == "log_heavy"),
        "bytes_gz": (out_dir / f"{version}.jsonl.gz").stat().st_size,
    }
    print(json.dumps(report), file=sys.stderr)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subset", required=True, help="INSTANCE:PROJECTS:FROM:TO")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--with-open-targets", action="store_true")
    args = parser.parse_args(argv)
    convert(
        SubsetSpec.parse(args.version, args.subset),
        args.out,
        args.version,
        args.with_open_targets,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
