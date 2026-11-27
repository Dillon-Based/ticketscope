"""Code-corpus feasibility: how many Mojang issues name the version that fixed them.

Throwaway measurement tooling, not product code. It streams the raw mongodump archive of
The Public Jira Dataset v7 from stdin (no MongoDB needed), reads the `Mojang` collection and
prints per-project counts of Fixed issues by fix version. With `--manifest` it also matches the
MC fix versions against Mojang's public version list and counts those released with official
obfuscation mappings (1.14.4, and every version from 19w36a on).

It prints aggregate counts and version names only: no issue text and no person data.

    curl -sS -o /tmp/manifest.json \
        https://piston-meta.mojang.com/mc/game/version_manifest_v2.json
    unzip -p "ThePublicJiraDataset.zip" \
        "ThePublicJiraDataset/3. DataDump/mongodump-JiraReposAnon.archive" | gzip -dc \
        | uv run python scripts/fixversion_coverage.py --manifest /tmp/manifest.json

Findings: `docs/code-corpus-feasibility.md`.
"""

import argparse
import json
import re
import statistics
import struct
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO

import bson

ARCHIVE_MAGIC = b"\x6d\xe2\x99\x81"
TERMINATOR = b"\xff\xff\xff\xff"
# The first versions Mojang published obfuscation mappings for.
FIRST_MAPPED_RELEASE = "1.14.4"
FIRST_MAPPED_SNAPSHOT_TIME = "2019-09-04"  # 19w36a


def _read(stream: BinaryIO, n: int) -> bytes:
    buf = stream.read(n)
    if len(buf) != n:
        raise EOFError
    return buf


def _next(stream: BinaryIO, decode: bool) -> dict[str, Any] | bool:
    """One archive item: False at a terminator, True for a skipped document, else the document."""
    head = _read(stream, 4)
    if head == TERMINATOR:
        return False
    (length,) = struct.unpack("<i", head)
    body = _read(stream, length - 4)
    return bson.decode(head + body) if decode else True


def collection_documents(stream: BinaryIO, collection: str) -> Iterator[dict[str, Any]]:
    """Yield the documents of one collection from a mongodump archive (already gunzipped)."""
    if _read(stream, 4) != ARCHIVE_MAGIC:
        raise ValueError("not a mongodump archive (is it still gzipped?)")
    while _next(stream, decode=False):  # prelude: header and collection metadata
        pass
    try:
        while True:
            header = _next(stream, decode=True)
            if not isinstance(header, dict) or header.get("EOF"):
                continue
            wanted = header.get("collection") == collection
            while True:
                doc = _next(stream, decode=wanted)
                if doc is False:
                    break
                if isinstance(doc, dict):
                    yield doc
    except EOFError:
        return


def _names(versions: Any) -> list[str]:
    return [v["name"] for v in versions or [] if v.get("name")]


def tally(stream: BinaryIO) -> dict[str, dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    by_version: dict[str, Counter[str]] = defaultdict(Counter)
    for doc in collection_documents(stream, "Mojang"):
        fields = doc.get("fields") or {}
        project = (fields.get("project") or {}).get("key") or "?"
        count = counts[project]
        count["total"] += 1
        resolution = (fields.get("resolution") or {}).get("name")
        if resolution is None:
            continue
        count["resolved"] += 1
        if resolution != "Fixed":
            continue
        count["fixed"] += 1
        fix = _names(fields.get("fixVersions"))
        if fix:
            count["fixed_with_fix_version"] += 1
        if len(fix) == 1:
            count["fixed_with_one_fix_version"] += 1
            by_version[project][fix[0]] += 1
    report: dict[str, dict[str, Any]] = {}
    for project, count in sorted(counts.items(), key=lambda kv: -kv[1]["total"]):
        sizes = sorted(by_version[project].values())
        report[project] = {
            **count,
            "fix_versions": len(sizes),
            "issues_per_fix_version_median": statistics.median(sizes) if sizes else None,
            "issues_per_fix_version_p90": sizes[int(len(sizes) * 0.9)] if sizes else None,
            "issues_per_fix_version_max": sizes[-1] if sizes else None,
            "by_fix_version": dict(by_version[project]),
        }
    return report


def _manifest_ids(name: str) -> Iterator[str]:
    """The manifest ids a Jira fix-version name may stand for."""
    name = re.sub(r"^Minecraft\s+", "", name.strip(), flags=re.IGNORECASE)
    yield name
    for word, tag in (("Pre-?release", "pre"), ("Release Candidate", "rc")):
        match = re.match(rf"^(\S+)\s+{word}\s*(\d+)$", name, flags=re.IGNORECASE)
        if match:
            yield f"{match.group(1)}-{tag}{match.group(2)}"


def mapped(by_fix_version: dict[str, int], manifest: dict[str, Any]) -> dict[str, Any]:
    """Count the fixed issues whose fix version was released with official mappings."""
    by_id = {v["id"].lower(): v for v in manifest["versions"]}
    matched = with_mappings = 0
    sizes: list[int] = []
    for name, issues in by_fix_version.items():
        version = next((by_id[i.lower()] for i in _manifest_ids(name) if i.lower() in by_id), None)
        if version is None:
            continue
        matched += issues
        if (
            version["id"] == FIRST_MAPPED_RELEASE
            or version["releaseTime"] >= FIRST_MAPPED_SNAPSHOT_TIME
        ):
            with_mappings += issues
            sizes.append(issues)
    sizes.sort()
    return {
        "issues_matched_to_manifest": matched,
        "issues_with_official_mappings": with_mappings,
        "versions_with_official_mappings": len(sizes),
        "issues_per_mapped_version_median": statistics.median(sizes) if sizes else None,
        "issues_per_mapped_version_p90": sizes[int(len(sizes) * 0.9)] if sizes else None,
        "issues_per_mapped_version_max": sizes[-1] if sizes else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--manifest", type=Path, help="Mojang version_manifest_v2.json")
    args = parser.parse_args()
    report = tally(sys.stdin.buffer)
    if args.manifest is not None and "MC" in report:
        manifest = json.loads(args.manifest.read_text())
        report["MC"]["mappings"] = mapped(report["MC"]["by_fix_version"], manifest)
    for project in report.values():
        del project["by_fix_version"]
    json.dump(report, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
