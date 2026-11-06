"""Spike 1.12: measure The Public Jira Dataset v7 against the corpus decision rule.

Spike evidence, not product code. Reads the dump restored into the throwaway MongoDB
container `jira-spike-mongo` (database `JiraReposAnon`, one collection per instance).

    uv run --with pymongo python measure.py --scope instance
    uv run --with pymongo python measure.py --scope project --instances Mojang,Jira
    uv run --with pymongo python measure.py --scope subset \
        --subset mojang-mc-2021=Mojang:MC:2021-01-01:2022-01-01
    uv run --with pymongo python measure.py --samples Mojang:MC:2021-01-01:2022-01-01 \
        --name mojang-mc-2021 [--pairs 10]

The subset of a scope is its resolved issues (resolution set), matching the epic's
"closed issues only". A pair is a `Duplicate`-resolved issue with a "duplicates"-type link
to another issue of the same subset; each unordered pair counts once, under the kind of
the duplicate issue. Kind is `ticketscope.core.derive.kind_score` (threshold 3) over the
description, with Jira `{code...}` and `{noformat}` toggles mapped onto fences.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ticketscope.core.derive import DEFAULT_KIND_THRESHOLD, kind_score
from ticketscope.jobs.ingest.mask import _EMAIL, _PEM_BLOCK, _SECRETS

HERE = Path(__file__).resolve().parent
MONGO_URI = "mongodb://127.0.0.1:27017"
DB = "JiraReposAnon"

# The dump's DataDefinition files, copied here (they are small and CC BY 4.0).
SOURCES = HERE / "jira_data_sources.json"
LINKTYPES = HERE / "jira_issue_linktype_mapping.json"

OUTCOMES = ("duplicate", "fixed", "not_planned", "stale", "answered", "unknown")

# --- outcome -------------------------------------------------------------------------------

# `resolution.name` (lower-cased) -> outcome. Anything else is `unknown` and listed as
# unmapped. `None` (unresolved) is `unknown` too, but is not "unmapped".
RESOLUTION_OUTCOME: dict[str, str] = {
    # duplicate
    "duplicate": "duplicate",
    "duplicate issue": "duplicate",
    # fixed: a change was made or the work was delivered
    "fixed": "fixed",
    "done": "fixed",
    "complete": "fixed",
    "implemented": "fixed",
    "resolved": "fixed",
    "fixed-verified": "fixed",
    "deployed": "fixed",
    "released": "fixed",
    "delivered": "fixed",
    "partially completed": "fixed",
    "staged": "fixed",
    "current release": "fixed",
    "next release": "fixed",
    # not_planned: closed without a change
    "won't fix": "not_planned",
    "won't do": "not_planned",
    "invalid": "not_planned",
    "incomplete": "not_planned",
    "incomplete description": "not_planned",
    "cannot reproduce": "not_planned",
    "works for me": "not_planned",
    "not a problem": "not_planned",
    "not a bug": "not_planned",
    "non-issue": "not_planned",
    "works as intended": "not_planned",
    "works as designed": "not_planned",
    "expected behavior": "not_planned",
    "rejected": "not_planned",
    "declined": "not_planned",
    "out of scope": "not_planned",
    "obsolete": "not_planned",
    "out of date": "not_planned",
    "gone away": "not_planned",
    "later": "not_planned",
    "deferred": "not_planned",
    "parked": "not_planned",
    "low priority": "not_planned",
    "deprioritized": "not_planned",
    "no resources": "not_planned",
    "won't finish": "not_planned",
    "will not implement": "not_planned",
    "canceled": "not_planned",
    "abandoned": "not_planned",
    "spam": "not_planned",
    "incorrectly filed": "not_planned",
    "invalid ticket": "not_planned",
    "not applicable": "not_planned",
    "unactionable": "not_planned",
    "unsolved mysteries": "not_planned",
    "eol": "not_planned",
    "incorporated": "not_planned",
    "tracked elsewhere": "not_planned",
    "moved": "not_planned",
    "migrated to another its": "not_planned",
    "resolved at apache": "not_planned",
    "upstream": "not_planned",
    "invalid: works as expected": "not_planned",
    "invalid: environment issue": "not_planned",
    "invalid: test error": "not_planned",
    "invalid: not supported": "not_planned",
    # stale: closed for want of a response
    "timed out": "stale",
    "awaiting response": "stale",
    "automatically closed": "stale",
    "auto closed": "stale",
    "low engagement": "stale",
    "pending closed": "stale",
    # answered: closed with an answer rather than a change
    "answered": "answered",
    "support request": "answered",
    "handled by support": "answered",
    "explained": "answered",
    "information provided": "answered",
    "community answered": "answered",
    "feedback received": "answered",
    "sent to forums": "answered",
    "sent to docs": "answered",
    "resolved locally": "answered",
    "workaround": "answered",
}

_QUESTION_TYPE = re.compile(r"question|support", re.IGNORECASE)


def map_resolution(name: str | None) -> tuple[str, bool]:
    """(outcome, mapped). Unresolved is ("unknown", True); an unmapped value ("unknown", False)."""
    if name is None:
        return "unknown", True
    outcome = RESOLUTION_OUTCOME.get(name.strip().lower())
    if outcome is None:
        return "unknown", False
    return outcome, True


def parse_time(value: str | None) -> datetime | None:
    """Jira `2021-12-28T20:34:52.000+0200` -> aware UTC datetime."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt).astimezone(UTC)
        except ValueError:
            continue
    raise ValueError(f"unparseable Jira time {value!r}")


def _user(person: Any) -> str | None:
    if not isinstance(person, dict):
        return None
    return person.get("key") or person.get("name") or person.get("accountId")


def comments_of(issue: dict[str, Any]) -> list[dict[str, Any]]:
    fields = issue.get("fields") or {}
    raw = fields.get("comments")
    if raw is None and isinstance(fields.get("comment"), dict):
        raw = fields["comment"].get("comments")
    return [c for c in (raw or []) if isinstance(c, dict)]


def is_answered(issue: dict[str, Any]) -> bool:
    """The "answered" rule: a Question/Support-type issue, resolved, with a comment at or
    before the resolution by someone other than the reporter (by masked id)."""
    fields = issue.get("fields") or {}
    itype = (fields.get("issuetype") or {}).get("name") or ""
    if not _QUESTION_TYPE.search(itype):
        return False
    resolved_at = parse_time(fields.get("resolutiondate"))
    if fields.get("resolution") is None or resolved_at is None:
        return False
    reporter = _user(fields.get("reporter"))
    for comment in comments_of(issue):
        author = _user(comment.get("author"))
        created = parse_time(comment.get("created"))
        if author and author != reporter and created is not None and created <= resolved_at:
            return True
    return False


def derive_outcome(issue: dict[str, Any]) -> tuple[str, str | None]:
    """(outcome, unmapped resolution name or None).

    Precedence: the resolution's class (duplicate, fixed, not_planned, stale, answered),
    except that a Question/Support-type issue whose resolution reads as fixed or is
    unmapped becomes `answered` when the answered rule holds: no code change closes a
    question.
    """
    fields = issue.get("fields") or {}
    name = (fields.get("resolution") or {}).get("name") if fields.get("resolution") else None
    outcome, mapped = map_resolution(name)
    if outcome in ("fixed", "unknown") and name is not None and is_answered(issue):
        return "answered", None
    return outcome, (None if mapped else name)


# --- kind ----------------------------------------------------------------------------------

_JIRA_BLOCK = re.compile(r"\{(?:code|noformat)(?::[^}\n]*)?\}", re.IGNORECASE)


def jira_to_fences(body: str | None) -> str | None:
    """Put every `{code...}` / `{noformat}` toggle on its own line as a ``` fence."""
    if body is None:
        return None
    return _JIRA_BLOCK.sub("\n```\n", body)


def extended_kind(body: str | None, threshold: int = DEFAULT_KIND_THRESHOLD) -> str:
    return "log_heavy" if kind_score(jira_to_fences(body)) >= threshold else "short"


# --- duplicate link ------------------------------------------------------------------------

_LINKTYPE_PREFIX = re.compile(r"^\s*\d+\s*-\s*")  # Sakai: "3 - Duplicate"


def load_linktype_map(path: Path = LINKTYPES) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))["link types"]


def is_duplicate_linktype(name: str | None, linkmap: dict[str, str]) -> bool:
    if not name:
        return False
    return linkmap.get(_LINKTYPE_PREFIX.sub("", name).strip()) == "Duplicate"


@dataclass(frozen=True, slots=True)
class DupLink:
    target: str  # issue key
    reversed: bool  # True when no link on this issue reads "duplicates" toward the target


def duplicate_target(issue: dict[str, Any], linkmap: dict[str, str]) -> DupLink | None:
    """The issue this one duplicates: the first "duplicates"-direction link of a
    Duplicate-mapped type; failing that, the first Duplicate-mapped link either way."""
    links = (issue.get("fields") or {}).get("issuelinks") or []
    fallback: DupLink | None = None
    for link in links:
        ltype = link.get("type") or {}
        if not is_duplicate_linktype(ltype.get("name"), linkmap):
            continue
        for side, text_key in (("outwardIssue", "outward"), ("inwardIssue", "inward")):
            other = link.get(side)
            if not isinstance(other, dict) or not other.get("key"):
                continue
            text = (ltype.get(text_key) or "").strip().lower()
            if text == "duplicates":
                return DupLink(other["key"], False)
            if fallback is None:
                fallback = DupLink(other["key"], True)
    return fallback


def is_duplicate_resolution(issue: dict[str, Any]) -> bool:
    res = (issue.get("fields") or {}).get("resolution") or {}
    return map_resolution(res.get("name"))[0] == "duplicate" if res else False


# --- hygiene -------------------------------------------------------------------------------

_WIKI = re.compile(
    r"\{code|\{noformat|\{quote|^\s*h[1-6]\.\s|\[[^\]|\n]+\|[^\]\n]+\]", re.MULTILINE
)
_MENTION = re.compile(r"\[~accountid:[^\]\n]+\]|\[~[^\]\n]+\]")
HYGIENE = ("wiki", "mention", "email", "secret", "nul")


def hygiene_flags(texts: Iterable[str | None]) -> set[str]:
    flags: set[str] = set()
    for text in texts:
        if not text:
            continue
        if "wiki" not in flags and _WIKI.search(text):
            flags.add("wiki")
        if "mention" not in flags and _MENTION.search(text):
            flags.add("mention")
        if "email" not in flags and _EMAIL.search(text):
            flags.add("email")
        if "secret" not in flags and (_PEM_BLOCK.search(text) or _SECRETS.search(text)):
            flags.add("secret")
        if "nul" not in flags and "\x00" in text:
            flags.add("nul")
    return flags


def issue_texts(issue: dict[str, Any]) -> list[str | None]:
    fields = issue.get("fields") or {}
    return [fields.get("summary"), fields.get("description")] + [
        c.get("body") for c in comments_of(issue)
    ]


# --- scope accumulator ---------------------------------------------------------------------


@dataclass
class Scope:
    instance: str
    project: str = ""
    keys: set[str] = field(default_factory=set)  # every issue in scope
    resolved: set[str] = field(default_factory=set)  # the subset
    dups: list[tuple[str, DupLink | None, str]] = field(default_factory=list)  # key, link, kind
    outcomes: Counter[str] = field(default_factory=Counter)
    kinds: Counter[str] = field(default_factory=Counter)
    types: Counter[str] = field(default_factory=Counter)
    reporters: Counter[str] = field(default_factory=Counter)
    hygiene: Counter[str] = field(default_factory=Counter)
    unmapped: Counter[str] = field(default_factory=Counter)
    created_min: datetime | None = None
    created_max: datetime | None = None
    repeated_docs: int = 0  # the dump holds a few issue keys more than once

    def add(self, issue: dict[str, Any], linkmap: dict[str, str]) -> None:
        key = issue["key"]
        fields = issue.get("fields") or {}
        if key in self.keys:
            self.repeated_docs += 1
            return
        self.keys.add(key)
        if fields.get("resolution") is None:
            return
        self.resolved.add(key)
        kind = extended_kind(fields.get("description"))
        self.kinds[kind] += 1
        outcome, unmapped = derive_outcome(issue)
        self.outcomes[outcome] += 1
        if unmapped:
            self.unmapped[unmapped] += 1
        self.types[(fields.get("issuetype") or {}).get("name") or "?"] += 1
        self.reporters[_user(fields.get("reporter")) or "?"] += 1
        for flag in hygiene_flags(issue_texts(issue)):
            self.hygiene[flag] += 1
        created = parse_time(fields.get("created"))
        if created is not None:
            self.created_min = min(filter(None, (self.created_min, created)))
            self.created_max = max(filter(None, (self.created_max, created)))
        if outcome == "duplicate":
            self.dups.append((key, duplicate_target(issue, linkmap), kind))

    def row(self) -> dict[str, Any]:
        n = len(self.resolved)
        in_subset: dict[frozenset[str], str] = {}
        to_open: dict[frozenset[str], str] = {}
        open_targets: set[str] = set()
        no_target = out_of_scope = link_reversed = 0
        for key, link, kind in self.dups:
            if link is None:
                no_target += 1
                continue
            if link.target == key or link.target not in self.keys:
                out_of_scope += 1
                continue
            pair = frozenset((key, link.target))
            if link.target in self.resolved:
                if pair not in in_subset:
                    in_subset[pair] = kind
                    link_reversed += link.reversed
            elif pair not in to_open:
                to_open[pair] = kind
                open_targets.add(link.target)
        both = {**to_open, **in_subset}
        unknown = self.outcomes["unknown"]
        top10 = sum(c for _, c in self.reporters.most_common(10))
        bug = sum(c for t, c in self.types.items() if t.lower() == "bug")
        qs = sum(c for t, c in self.types.items() if _QUESTION_TYPE.search(t))
        n_open = n + len(open_targets)
        return {
            "instance": self.instance,
            "project": self.project,
            "issues_total": len(self.keys),
            "repeated_docs": self.repeated_docs,
            "issues_resolved": n,
            "short": self.kinds["short"],
            "log_heavy": self.kinds["log_heavy"],
            "dup_resolved": len(self.dups),
            "pairs": len(in_subset),
            "pairs_short": sum(1 for k in in_subset.values() if k == "short"),
            "pairs_log_heavy": sum(1 for k in in_subset.values() if k == "log_heavy"),
            "pairs_link_reversed": link_reversed,
            "pairs_target_open": len(to_open),
            "pairs_out_of_scope": out_of_scope,
            "dup_no_target": no_target,
            **{f"share_{o}": _share(self.outcomes[o], n) for o in OUTCOMES},
            "plus_open_targets_issues": n_open,
            "plus_open_targets_pairs": len(both),
            "plus_open_targets_pairs_short": sum(1 for k in both.values() if k == "short"),
            "plus_open_targets_pairs_log_heavy": sum(1 for k in both.values() if k == "log_heavy"),
            "plus_open_targets_share_unknown": _share(unknown + len(open_targets), n_open),
            "type_bug": _share(bug, n),
            "type_question_support": _share(qs, n),
            "top_types": "; ".join(f"{t}={c}" for t, c in self.types.most_common(5)),
            "reporters_distinct": len(self.reporters),
            "reporters_top10_share": _share(top10, n),
            **{f"hyg_{h}": self.hygiene[h] for h in HYGIENE},
            "unmapped_resolutions": "; ".join(f"{r}={c}" for r, c in self.unmapped.most_common()),
            "created_min": self.created_min.date().isoformat() if self.created_min else "",
            "created_max": self.created_max.date().isoformat() if self.created_max else "",
        }


def _share(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0


# --- mongo ---------------------------------------------------------------------------------

PROJECTION = {
    "_id": 0,
    "id": 1,
    "key": 1,
    "fields.summary": 1,
    "fields.description": 1,
    "fields.resolution.name": 1,
    "fields.resolutiondate": 1,
    "fields.created": 1,
    "fields.updated": 1,
    "fields.issuetype.name": 1,
    "fields.project.key": 1,
    "fields.reporter.key": 1,
    "fields.reporter.name": 1,
    "fields.reporter.accountId": 1,
    "fields.labels": 1,
    "fields.status.name": 1,
    "fields.issuelinks.type": 1,
    "fields.issuelinks.outwardIssue.key": 1,
    "fields.issuelinks.inwardIssue.key": 1,
    "fields.comments.body": 1,
    "fields.comments.created": 1,
    "fields.comments.author.key": 1,
    "fields.comments.author.name": 1,
    "fields.comments.author.accountId": 1,
}


def _db() -> Any:
    from pymongo import MongoClient

    return MongoClient(MONGO_URI)[DB]


def iter_issues(instance: str, query: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    cursor = _db()[instance].find(query or {}, PROJECTION, no_cursor_timeout=True)
    try:
        yield from cursor
    finally:
        cursor.close()


@dataclass(frozen=True, slots=True)
class SubsetSpec:
    name: str
    instance: str
    projects: frozenset[str]  # empty: all projects
    created_from: datetime | None
    created_to: datetime | None  # exclusive

    @classmethod
    def parse(cls, name: str, spec: str) -> SubsetSpec:
        """`INSTANCE:PROJ1,PROJ2:FROM:TO`; projects and dates may be empty."""
        parts = [*spec.split(":"), "", "", ""][:4]
        instance, projects, start, end = parts
        return cls(
            name,
            instance,
            frozenset(p for p in projects.split(",") if p),
            datetime.fromisoformat(start).replace(tzinfo=UTC) if start else None,
            datetime.fromisoformat(end).replace(tzinfo=UTC) if end else None,
        )

    def contains(self, issue: dict[str, Any]) -> bool:
        fields = issue.get("fields") or {}
        project = (fields.get("project") or {}).get("key") or issue["key"].split("-")[0]
        if self.projects and project not in self.projects:
            return False
        if self.created_from or self.created_to:
            created = parse_time(fields.get("created"))
            if created is None:
                return False
            if self.created_from and created < self.created_from:
                return False
            if self.created_to and created >= self.created_to:
                return False
        return True

    def query(self) -> dict[str, Any]:
        return {"fields.project.key": {"$in": sorted(self.projects)}} if self.projects else {}


def measure_instance(instance: str, by_project: bool, linkmap: dict[str, str]) -> list[dict]:
    whole = Scope(instance)
    projects: dict[str, Scope] = {}
    for i, issue in enumerate(iter_issues(instance), start=1):
        whole.add(issue, linkmap)
        if by_project:
            pkey = ((issue.get("fields") or {}).get("project") or {}).get("key") or "?"
            projects.setdefault(pkey, Scope(instance, pkey)).add(issue, linkmap)
        if i % 100_000 == 0:
            print(f"  {instance}: {i} issues", file=sys.stderr, flush=True)
    if by_project:
        return [p.row() for p in sorted(projects.values(), key=lambda s: s.project)]
    return [whole.row()]


def measure_subset(spec: SubsetSpec, linkmap: dict[str, str]) -> dict[str, Any]:
    scope = Scope(spec.instance, spec.name)
    for issue in iter_issues(spec.instance, spec.query()):
        if spec.contains(issue):
            scope.add(issue, linkmap)
    return scope.row()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)", file=sys.stderr)


# --- samples -------------------------------------------------------------------------------


def _cell(text: str | None, limit: int = 160) -> str:
    flat = re.sub(r"\s+", " ", text or "").strip()
    flat = flat if len(flat) <= limit else flat[: limit - 1] + "…"
    return flat.replace("|", "\\|")


def _browse(instance: str, key: str) -> str:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    return f"{sources[instance]['jira_url'].rstrip('/')}/browse/{key}"


def changelog_confirms(issue: dict[str, Any], target: str) -> tuple[bool, bool]:
    """(resolution set to a duplicate value, a link to `target` added) per the changelog."""
    res = link = False
    for history in (issue.get("changelog") or {}).get("histories") or []:
        for item in history.get("items") or []:
            fname = (item.get("field") or "").lower()
            if fname == "resolution" and map_resolution(item.get("toString"))[0] == "duplicate":
                res = True
            if fname == "link" and item.get("to") == target:
                link = True
    return res, link


def write_samples(spec: SubsetSpec, n: int, pairs: int, linkmap: dict[str, str]) -> Path:
    rng = random.Random(12)
    first: dict[str, dict[str, Any]] = {}
    for i in iter_issues(spec.instance, spec.query()):
        if spec.contains(i):
            first.setdefault(i["key"], i)  # the first document wins, as in Scope.add
    scoped = list(first.values())
    resolved = [i for i in scoped if (i.get("fields") or {}).get("resolution") is not None]
    picked = rng.sample(resolved, min(n, len(resolved)))
    lines = [
        f"# Samples: {spec.name}",
        "",
        f"Subset: instance `{spec.instance}`, projects "
        f"`{','.join(sorted(spec.projects)) or 'all'}`, created "
        f"{spec.created_from.date() if spec.created_from else '…'} to "
        f"{spec.created_to.date() if spec.created_to else '…'} (exclusive), resolved issues "
        f"only: {len(resolved)} issues. {len(picked)} drawn with `random.Random(12)`.",
        "",
        "Kind is the extended kind rule; outcome is the proposed mapping "
        "(`outcome-mapping.md`). Text is the first 160 characters of the description.",
        "",
        "| # | Issue | Type | Resolution | Outcome | Kind | Title | Description | "
        "Author judgement |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for idx, issue in enumerate(picked, start=1):
        f = issue["fields"]
        outcome, _ = derive_outcome(issue)
        lines.append(
            f"| {idx} | [{issue['key']}]({_browse(spec.instance, issue['key'])}) | "
            f"{(f.get('issuetype') or {}).get('name', '')} | {f['resolution'].get('name')} | "
            f"{outcome} | {extended_kind(f.get('description'))} | {_cell(f.get('summary'), 90)} "
            f"| {_cell(f.get('description'))} |  |"
        )
    if pairs:
        lines += _pair_samples(spec, scoped, pairs, rng, linkmap)
    path = HERE / f"samples-{spec.name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)
    return path


def _pair_samples(
    spec: SubsetSpec,
    scoped: list[dict[str, Any]],
    n: int,
    rng: random.Random,
    linkmap: dict[str, str],
) -> list[str]:
    """Pairs of the "+ open targets" subset: a resolved duplicate whose target is any issue
    of the scope, resolved or not. Each unordered pair counts once (first seen wins)."""
    by_key = {i["key"]: i for i in scoped}  # first-wins documents, every state
    seen: set[frozenset[str]] = set()
    candidates = []
    for issue in scoped:
        if (issue.get("fields") or {}).get("resolution") is None:
            continue
        if not is_duplicate_resolution(issue):
            continue
        link = duplicate_target(issue, linkmap)
        if not link or link.target not in by_key or link.target == issue["key"]:
            continue
        pair = frozenset((issue["key"], link.target))
        if pair not in seen:
            seen.add(pair)
            candidates.append((issue, link))
    chosen = rng.sample(candidates, min(n, len(candidates)))
    coll = _db()[spec.instance]
    out = [
        "",
        f"## Duplicate pairs ({len(chosen)} of {len(candidates)} in-subset pairs, "
        "unresolved targets included)",
        "",
        "Each pair checked against the duplicate issue's changelog in the dump: was the "
        "resolution set to Duplicate, and was a link to the target added? Titles are shown "
        "for a reader's judgement of whether the pair really is a duplicate.",
        "",
        "| # | Duplicate | Target | Target resolution | Kind | Changelog: resolution | "
        "Changelog: link | Duplicate title | Target title | Author judgement |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for idx, (issue, link) in enumerate(chosen, start=1):
        full = coll.find_one({"key": issue["key"]}, {"changelog": 1}) or {}
        res, lnk = changelog_confirms(full, link.target)
        target = by_key[link.target]
        target_res = (target["fields"].get("resolution") or {}).get("name") or "unresolved"
        out.append(
            f"| {idx} | [{issue['key']}]({_browse(spec.instance, issue['key'])}) | "
            f"[{link.target}]({_browse(spec.instance, link.target)}) | {target_res} | "
            f"{extended_kind(issue['fields'].get('description'))} | "
            f"{'yes' if res else 'no'} | {'yes' if lnk else 'no'} | "
            f"{_cell(issue['fields'].get('summary'), 90)} | "
            f"{_cell(target['fields'].get('summary'), 90)} |  |"
        )
    return out


# --- cli -----------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scope", choices=("instance", "project", "subset"))
    parser.add_argument("--instances", default="", help="comma list; default all")
    parser.add_argument(
        "--subset", action="append", default=[], help="NAME=INSTANCE:PROJECTS:FROM:TO"
    )
    parser.add_argument("--samples", help="INSTANCE:PROJECTS:FROM:TO to sample from")
    parser.add_argument("--name", help="candidate name for --samples")
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--pairs", type=int, default=0)
    args = parser.parse_args(argv)
    linkmap = load_linktype_map()

    if args.samples:
        write_samples(SubsetSpec.parse(args.name, args.samples), args.n, args.pairs, linkmap)
        return 0

    if args.scope == "subset":
        rows = []
        for item in args.subset:
            name, spec = item.split("=", 1)
            print(f"subset {name}", file=sys.stderr, flush=True)
            rows.append(measure_subset(SubsetSpec.parse(name, spec), linkmap))
        write_csv(HERE / "subsets.csv", rows)
        return 0

    instances = [i for i in args.instances.split(",") if i] or sorted(_db().list_collection_names())
    by_project = args.scope == "project"
    rows: list[dict[str, Any]] = []
    for instance in instances:
        print(f"instance {instance}", file=sys.stderr, flush=True)
        rows += measure_instance(instance, by_project, linkmap)
    write_csv(HERE / ("projects.csv" if by_project else "instances.csv"), rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
