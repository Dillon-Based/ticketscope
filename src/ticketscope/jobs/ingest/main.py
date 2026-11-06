"""ingest: the only GitHub API caller (AD-6). Builds a corpus snapshot of closed issues.

One pass:

1. Select. Unless `<work>/selected.json` exists, list closed issues updated since the
   window start, keep issues (not PRs) closed in the window and not excluded, newest
   closed first, capped; mask them and checkpoint the list.
2. Enrich. For each selected issue not yet in `<work>/fetched.jsonl`, page its timeline
   into comments and events, mask, append one line and flush.
3. Write. With every issue fetched, write `<out>/<version>.jsonl.gz`, its `.sha256`,
   the `<version>-kinds.json` sidecar for the timed load, and `report.json`.

Exit codes: 0 complete, 3 the deadline passed (checkpoint saved; run again to resume),
1 failure, 2 bad usage.
"""

import argparse
import gzip
import hashlib
import json
import logging
import os
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from ticketscope.adapters.github import DeadlineReached, GitHubClient, GitHubGone
from ticketscope.core.derive import DEFAULT_KIND_THRESHOLD, derive_kind
from ticketscope.core.snapshot import SCHEMA_VERSION, SnapshotIssue
from ticketscope.jobs.ingest.select import enrich, select_issues
from ticketscope.settings import Settings

log = logging.getLogger("ticketscope.ingest")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_DEADLINE = 3

DEFAULT_REPO = "kubernetes/kubernetes"
DEFAULT_WINDOW_DAYS = 1095
DEFAULT_CAP = 20_000
SELECTED = "selected.json"
FETCHED = "fetched.jsonl"
GONE = "gone.txt"
REPORT = "report.json"


@dataclass(frozen=True, slots=True)
class Options:
    version: str
    work_dir: Path
    out_dir: Path
    exclusions: Path
    repo: str = DEFAULT_REPO
    window_days: int = DEFAULT_WINDOW_DAYS
    cap: int = DEFAULT_CAP


@dataclass(frozen=True, slots=True)
class Selection:
    repo: str
    window_start: datetime
    window_end: datetime
    window_days: int
    cap: int
    excluded: int
    issues: list[SnapshotIssue]


# --- exclusions ----------------------------------------------------------------------------


def read_exclusions(path: Path) -> frozenset[int]:
    """Issue numbers, one per line; `#` starts a comment."""
    numbers: set[int] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        if not text.isdigit() or int(text) < 1:
            raise ValueError(f"{path}:{lineno}: expected an issue number, got {text!r}")
        numbers.add(int(text))
    return frozenset(numbers)


# --- checkpoint ----------------------------------------------------------------------------


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def save_selection(work_dir: Path, selection: Selection) -> None:
    doc = {
        "repo": selection.repo,
        "window": {
            "start": _iso(selection.window_start),
            "end": _iso(selection.window_end),
            "days": selection.window_days,
        },
        "cap": selection.cap,
        "excluded": selection.excluded,
        "issues": [issue.model_dump(mode="json") for issue in selection.issues],
    }
    _write_atomic(work_dir / SELECTED, json.dumps(doc, ensure_ascii=False).encode())


def load_selection(work_dir: Path) -> Selection | None:
    path = work_dir / SELECTED
    if not path.exists():
        return None
    doc = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    window = cast(dict[str, Any], doc["window"])
    return Selection(
        repo=str(doc["repo"]),
        window_start=datetime.fromisoformat(str(window["start"])),
        window_end=datetime.fromisoformat(str(window["end"])),
        window_days=int(window["days"]),
        cap=int(doc["cap"]),
        excluded=int(doc["excluded"]),
        issues=[SnapshotIssue.model_validate(raw) for raw in doc["issues"]],
    )


def read_gone(path: Path) -> set[int]:
    """Issues found deleted, hidden or transferred during enrichment."""
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    # Text after the last newline never finished writing.
    complete = text[: text.rfind("\n") + 1]
    return {int(line) for line in complete.split() if line.isdigit()}


def load_fetched(path: Path) -> dict[int, SnapshotIssue]:
    """Issues already fetched. A partial or corrupt trailing line is dropped from the file."""
    if not path.exists():
        return {}
    data = path.read_bytes()
    fetched: dict[int, SnapshotIssue] = {}
    good_end = 0
    lines = data.split(b"\n")
    # Bytes after the last newline never finished writing.
    complete, partial = lines[:-1], lines[-1]
    for index, line in enumerate(complete):
        try:
            issue = SnapshotIssue.model_validate_json(line)
        except ValueError:
            if index == len(complete) - 1:
                log.warning("%s: corrupt trailing line dropped", path)
                break
            raise ValueError(f"{path}:{index + 1}: corrupt checkpoint line") from None
        fetched[issue.number] = issue
        good_end += len(line) + 1
    if partial or good_end != len(data):
        if partial:
            log.warning("%s: partial trailing line dropped", path)
        with path.open("r+b") as f:
            f.truncate(good_end)
    return fetched


# --- passes --------------------------------------------------------------------------------


def _select(client: GitHubClient, options: Options, now: datetime) -> Selection:
    window_end = now
    window_start = now - timedelta(days=options.window_days)
    exclusions = read_exclusions(options.exclusions)
    params: dict[str, str | int] = {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        "since": _iso(window_start),
        "per_page": 100,
    }

    def listed() -> Iterator[dict[str, Any]]:
        for page in client.get_pages(f"/repos/{options.repo}/issues", params):
            yield from page

    issues, excluded = select_issues(
        listed(),
        repo=options.repo,
        window_start=window_start,
        cap=options.cap,
        exclusions=exclusions,
    )
    log.info(
        "selected %d issues closed %s..%s (%d excluded)",
        len(issues),
        _iso(window_start),
        _iso(window_end),
        excluded,
    )
    return Selection(
        repo=options.repo,
        window_start=window_start,
        window_end=window_end,
        window_days=options.window_days,
        cap=options.cap,
        excluded=excluded,
        issues=issues,
    )


def _timeline(client: GitHubClient, repo: str, number: int) -> Iterator[dict[str, Any]]:
    for page in client.get_pages(f"/repos/{repo}/issues/{number}/timeline", {"per_page": 100}):
        yield from page


def run(options: Options, client: GitHubClient, clock: Callable[[], float] = time.time) -> int:
    """One ingest pass. Returns an exit code."""
    options.work_dir.mkdir(parents=True, exist_ok=True)
    exclusions = read_exclusions(options.exclusions)
    try:
        selection = load_selection(options.work_dir)
        if selection is None:
            now = datetime.fromtimestamp(clock(), UTC).replace(microsecond=0)
            selection = _select(client, options, now)
            save_selection(options.work_dir, selection)
        elif (selection.repo, selection.window_days, selection.cap) != (
            options.repo,
            options.window_days,
            options.cap,
        ):
            log.warning("resuming the checkpointed selection; its repo, window and cap win")

        fetched_path = options.work_dir / FETCHED
        fetched = load_fetched(fetched_path)
        gone_path = options.work_dir / GONE
        gone = read_gone(gone_path)
        todo = [
            issue
            for issue in selection.issues
            if issue.number not in fetched
            and issue.number not in exclusions
            and issue.number not in gone
        ]
        log.info("%d issues fetched, %d gone, %d to go", len(fetched), len(gone), len(todo))
        with (
            fetched_path.open("a", encoding="utf-8") as out,
            gone_path.open("a", encoding="utf-8") as gone_out,
        ):
            for done, base in enumerate(todo, start=1):
                try:
                    issue = enrich(base, _timeline(client, selection.repo, base.number))
                except GitHubGone as exc:
                    # Deleted, hidden or transferred since listing: leave it out for good.
                    log.warning("issue %d is gone, left out: %s", base.number, exc)
                    gone_out.write(f"{base.number}\n")
                    gone_out.flush()
                    gone.add(base.number)
                    continue
                out.write(issue.model_dump_json() + "\n")
                out.flush()
                fetched[issue.number] = issue
                if done % 100 == 0:
                    log.info("fetched %d/%d", done, len(todo))
    except DeadlineReached:
        log.warning("deadline reached; checkpoint saved, run again to resume")
        return EXIT_DEADLINE

    issues = [
        fetched[issue.number]
        for issue in selection.issues
        if issue.number not in exclusions and issue.number not in gone
    ]
    # Numbers added to the exclusion list after selection count too.
    excluded = selection.excluded + sum(1 for i in selection.issues if i.number in exclusions)
    write_outputs(
        options.out_dir,
        options.version,
        selection,
        issues,
        excluded=excluded,
        gone=sum(1 for i in selection.issues if i.number in gone and i.number not in exclusions),
    )
    return EXIT_OK


# --- outputs -------------------------------------------------------------------------------


def write_outputs(
    out_dir: Path,
    version: str,
    selection: Selection,
    issues: list[SnapshotIssue],
    *,
    excluded: int,
    gone: int = 0,
) -> dict[str, Any]:
    """The asset, its checksum, the kinds sidecar (for the timed load only) and the report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    asset = f"{version}.jsonl.gz"
    payload = "".join(issue.model_dump_json() + "\n" for issue in issues).encode("utf-8")
    # mtime=0 and no file name: the same issues give the same bytes.
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    digest = hashlib.sha256(compressed).hexdigest()
    _write_atomic(out_dir / asset, compressed)
    _write_atomic(out_dir / f"{asset}.sha256", f"{digest}  {asset}\n".encode())

    kinds = {str(issue.number): derive_kind(issue) for issue in issues}
    _write_atomic(out_dir / f"{version}-kinds.json", json.dumps(kinds, indent=0).encode())

    report: dict[str, Any] = {
        "version": version,
        "schema_version": SCHEMA_VERSION,
        "repo": selection.repo,
        "window": {
            "start": _iso(selection.window_start),
            "end": _iso(selection.window_end),
            "days": selection.window_days,
        },
        "cap": selection.cap,
        "count": len(issues),
        "excluded": excluded,
        "gone": gone,
        "kind_threshold": DEFAULT_KIND_THRESHOLD,
        "kinds": {
            "short": sum(1 for kind in kinds.values() if kind == "short"),
            "log_heavy": sum(1 for kind in kinds.values() if kind == "log_heavy"),
        },
        "asset": asset,
        "sha256": digest,
    }
    _write_atomic(out_dir / REPORT, (json.dumps(report, indent=2) + "\n").encode())
    log.info(
        "wrote %s: %d issues (%d short, %d log_heavy)",
        asset,
        report["count"],
        report["kinds"]["short"],
        report["kinds"]["log_heavy"],
    )
    return report


# --- entry point ---------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ticketscope-ingest", description=__doc__)
    parser.add_argument("--version", required=True, help="snapshot version, YYYY.MM.N")
    parser.add_argument("--work-dir", type=Path, default=Path("work"))
    parser.add_argument("--out-dir", type=Path, default=Path("out"))
    parser.add_argument("--exclusions", type=Path, default=Path("snapshot/exclusions.txt"))
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    parser.add_argument("--cap", type=int, default=DEFAULT_CAP)
    parser.add_argument(
        "--deadline-minutes",
        type=float,
        default=None,
        help="stop with exit 3 and a checkpoint once this many minutes have passed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parser().parse_args(argv)
    if args.window_days < 1 or args.cap < 1:
        log.error("--window-days and --cap must be at least 1")
        return EXIT_USAGE
    token = Settings().ingest_github_token.get_secret_value()
    if not token:
        log.error("TICKETSCOPE_INGEST_GITHUB_TOKEN is not set")
        return EXIT_USAGE
    options = Options(
        version=args.version,
        work_dir=args.work_dir,
        out_dir=args.out_dir,
        exclusions=args.exclusions,
        repo=args.repo,
        window_days=args.window_days,
        cap=args.cap,
    )
    deadline = None if args.deadline_minutes is None else time.time() + args.deadline_minutes * 60
    client = GitHubClient(token, deadline=deadline)
    try:
        return run(options, client)
    except Exception:
        log.exception("ingest failed")
        return EXIT_FAILED
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
