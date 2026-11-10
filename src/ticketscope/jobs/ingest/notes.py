"""Release notes of a corpus snapshot, from ingest's `report.json` (AD-6, AD-12).

    uv run python -m ticketscope.jobs.ingest.notes --report out/report.json \
        --load-seconds 4.2 --commit "$(git rev-parse HEAD)" --repo owner/name > notes.md

Refuses (exit 1) a load time over the 600 s budget, so no Release is created for it.

The embedding asset has its own Release and notes, from the manifest `embed` writes:

    uv run python -m ticketscope.jobs.ingest.notes --embeddings-manifest out/<tag>.manifest.json \
        --load-seconds 95.0 --commit "$(git rev-parse HEAD)" > notes.md
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

LOAD_BUDGET_SECONDS = 600.0

# Spike 12's attribution line (`terms.md`, "Draft attribution line"), word for word.
ATTRIBUTION = (
    "Issue text from the Mojang bug tracker (bugs.mojang.com), as collected in The Public "
    "Jira Dataset v7 by Lloyd Montgomery, Clara Lüders and Walid Maalej (Zenodo, "
    'doi:10.5281/zenodo.15719919, CC BY 4.0), described in "An Alternative Issue Tracking '
    'Dataset of Public Jira Repositories", MSR 2022, pp. 73–77. The text belongs to its '  # noqa: RUF001
    "authors; each record links to its source issue. Data collected in January 2022; "
    "changes to source issues after that date are not reflected."
)


def render_notes(
    report: dict[str, Any], load_seconds: float, commit: str, repo: str | None = None
) -> str:
    """Markdown notes: subset, counts, pairs by kind, kind split, load time, attribution."""
    if not math.isfinite(load_seconds) or load_seconds < 0:
        raise ValueError(f"load time must be a non-negative number, got {load_seconds}")
    if load_seconds > LOAD_BUDGET_SECONDS:
        raise ValueError(f"load took {load_seconds} s, over the {LOAD_BUDGET_SECONDS:g} s budget")
    subset = report["subset"]
    projects = ", ".join(subset["projects"])
    kinds = report["kinds"]
    pairs = report["pairs"]
    issues_link = f"[{repo}](https://github.com/{repo}/issues)" if repo else "this repository"
    lines = [
        f"Corpus snapshot {report['version']} (schema v{report['schema_version']}): "
        f"{subset['instance']} projects {projects}, {subset['rule']}.",
        "",
        f"- Built from commit `{commit}`",
        f"- Issues: {report['count']} ({report['open_targets']} unresolved duplicate targets; "
        f"{report['excluded']} excluded by the takedown list; "
        f"{report['repeated_keys_dropped']} repeated dump documents dropped; "
        f"{report['bad_time_skipped']} skipped for an unparseable time; "
        f"{report['resolved_without_date']} resolved without a resolution date)",
        f"- In-subset duplicate pairs: {pairs['total']} "
        f"({pairs['short']} short, {pairs['log_heavy']} log-heavy)",
        f"- Kind split at threshold {report['kind_threshold']}: "
        f"{kinds['short']} short, {kinds['log_heavy']} log-heavy",
        f"- Timed load into the in-repo Postgres image: {load_seconds:g} s "
        f"(budget {LOAD_BUDGET_SECONDS:g} s)",
        f"- SHA-256: `{report['sha256']}` (`sha256sum -c {report['asset']}.sha256`)",
        "",
        "## Attribution",
        "",
        ATTRIBUTION,
        "",
        "No reporter, assignee, creator or comment-author id is stored; a comment keeps only "
        "whether the reporter wrote it. `[~user]` and `[~accountid:…]` mentions are replaced "
        "with `[~user]`, email addresses with `[email masked]`, and token- or key-shaped "
        "secrets with `[secret masked]`.",
        "",
        "## Takedown",
        "",
        f"To have an issue removed, open an issue in {issues_link} with its key (such as "
        "`MCL-123`). It goes on `snapshot/exclusions.txt`, the next version leaves it out, "
        "and the earlier Release assets that hold it are deleted. See the README section "
        '"Corpus attribution and takedown".',
    ]
    return "\n".join(lines) + "\n"


def render_embedding_notes(manifest: dict[str, Any], load_seconds: float, commit: str) -> str:
    """Markdown notes of an embedding asset: what it was built from, counts, the timed load
    (asset download and bulk load) and the attribution. Refuses a load over the budget."""
    if not math.isfinite(load_seconds) or load_seconds < 0:
        raise ValueError(f"load time must be a non-negative number, got {load_seconds}")
    if load_seconds > LOAD_BUDGET_SECONDS:
        raise ValueError(f"load took {load_seconds} s, over the {LOAD_BUDGET_SECONDS:g} s budget")
    runtime = ", ".join(
        f"{name} {version}" for name, version in sorted(manifest["runtime"].items())
    )
    lines = [
        f"Embeddings of corpus snapshot {manifest['snapshot']} from {manifest['model_id']}, "
        f"preprocessing {manifest['preprocessing_version']}.",
        "",
        f"- Built from commit `{commit}`, from the checksum-verified published snapshot",
        f"- Vectors: {manifest['count']}, {manifest['dimension']} dimensions each "
        f"({manifest['embed_seconds']:g} s in the model)",
        f"- Model file SHA-256: `{manifest['model_sha256']}`",
        f"- Runtime: {runtime}",
        f"- Timed load into the in-repo Postgres image, with the asset download and bulk load: "
        f"{load_seconds:g} s (budget {LOAD_BUDGET_SECONDS:g} s)",
        f"- SHA-256: `{manifest['sha256']}` (`sha256sum -c {manifest['asset']}.sha256`)",
        "",
        "The asset holds only the issue number, the model id and the vector of each issue, "
        "and a manifest on its first line. It holds no text, key, link or person identifier.",
        "",
        "## Pin",
        "",
        f"A person merges `embeddings.assetVersion: {manifest['snapshot']}` and "
        f"`embeddings.sha256: {manifest['sha256']}` into `values.yaml`.",
        "",
        "## Attribution",
        "",
        ATTRIBUTION,
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a snapshot's Release notes.")
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--embeddings-manifest", type=Path, help="render an embedding asset's notes"
    )
    parser.add_argument("--load-seconds", type=float, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repo", default=None, help="owner/name, for the takedown link")
    args = parser.parse_args(argv)
    if (args.report is None) == (args.embeddings_manifest is None):
        parser.error("give exactly one of --report and --embeddings-manifest")
    try:
        if args.embeddings_manifest is not None:
            manifest = json.loads(args.embeddings_manifest.read_text(encoding="utf-8"))
            notes = render_embedding_notes(manifest, args.load_seconds, args.commit)
        else:
            report = json.loads(args.report.read_text(encoding="utf-8"))
            notes = render_notes(report, args.load_seconds, args.commit, args.repo)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
