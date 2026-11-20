#!/usr/bin/env python3
"""Classify AWS listings for the env-down leftover check (story 5.4, R3).

    python3 scripts/leftover_check.py [--list] [--dry-run] [--candidates]
                                      [--confirmations TSV] [--environment eks]
                                      [--cluster ticketscope-env] FILE [FILE ...]

Each FILE is the JSON of one read-only AWS listing: `aws resourcegroupstaggingapi get-resources`
(key `ResourceTagMappingList`) or `aws ec2 describe-network-interfaces` (key `NetworkInterfaces`).
A resource is a leftover when its `environment` tag is the environment's (or the load balancer
controller's `elbv2.k8s.aws/cluster` tag is the cluster's, or it is a VPC CNI interface: tagged
`eks:eni:owner=amazon-vpc-cni` and `cluster.k8s.amazonaws.com/name` of the cluster) and it is not
`stack=bootstrap`.

Exit 0 when nothing is left, 1 when something is (each is named), 2 when a listing cannot be
trusted: unreadable, malformed, missing its key or empty. An unreadable listing never reads as
clean. `--list` prints what is found and exits 0 unless a listing is untrustworthy. `--dry-run`
reads no file: it injects one tagged load balancer, so the run must fail and name it.

The tagging API lags: it listed removed volumes for at least four minutes after the env stack
was torn down. So scripts/leftover-check.sh confirms each candidate with its own service. It runs
`--candidates` first (prints `<type>\t<id>` per candidate, exit 0), makes one read-only describe
call per candidate, and passes the answers back as `--confirmations`: a TSV of `<id>\t<status>`,
status `gone`, `found`, `error` or `unconfirmed`. Only `gone` drops a candidate, printed as
`GONE <type> <id> (tagging API lag)`; any other status, or none, keeps it a leftover. This module
makes no call itself.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ENV_TAG = "environment"
CLUSTER_TAG = "elbv2.k8s.aws/cluster"
CNI_OWNER_TAG = ("eks:eni:owner", "amazon-vpc-cni")
CNI_CLUSTER_TAG = "cluster.k8s.amazonaws.com/name"
BOOTSTRAP_TAG = ("stack", "bootstrap")
ENI_PREFIX = "ec2:network-interface/"
DRY_RUN_ARN = "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/dry-run/0"

Row = tuple[str, dict[str, str]]


class ListingError(Exception):
    """A listing that cannot be trusted; the check fails on it."""


def _tags(raw: object, where: str) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, list):
        raise ListingError(f"{where}: tags are not a list")
    tags: dict[str, str] = {}
    for tag in raw:
        if not isinstance(tag, dict) or "Key" not in tag:
            raise ListingError(f"{where}: malformed tag")
        tags[str(tag["Key"])] = str(tag.get("Value", ""))
    return tags


def classify(arn: str) -> str:
    """`<service>:<type>` from an ARN, e.g. `elasticloadbalancing:loadbalancer`."""
    if arn.startswith(ENI_PREFIX):
        return "ec2:network-interface"
    parts = arn.split(":", 5)
    if len(parts) < 6:
        return "unknown"
    resource = parts[5]
    # The type ends at the first `/` or `:` (`volume/vol-1`, `log-group:/aws/eks/...`).
    kind = re.split(r"[/:]", resource, maxsplit=1)[0]
    return f"{parts[2]}:{kind}"


def read_listing(path: Path) -> list[Row]:
    """(ARN or id, tags) of every resource in one listing file."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ListingError(f"{path}: unreadable listing ({error})") from error
    if not isinstance(doc, dict):
        raise ListingError(f"{path}: listing is not a JSON object")
    rows: list[Row] = []
    if "ResourceTagMappingList" in doc:
        items = doc["ResourceTagMappingList"]
        if not isinstance(items, list):
            raise ListingError(f"{path}: ResourceTagMappingList is not a list")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("ResourceARN"), str):
                raise ListingError(f"{path}: a row has no ResourceARN")
            rows.append((item["ResourceARN"], _tags(item.get("Tags"), str(path))))
        return rows
    if "NetworkInterfaces" in doc:
        items = doc["NetworkInterfaces"]
        if not isinstance(items, list):
            raise ListingError(f"{path}: NetworkInterfaces is not a list")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("NetworkInterfaceId"), str):
                raise ListingError(f"{path}: a row has no NetworkInterfaceId")
            ident = ENI_PREFIX + item["NetworkInterfaceId"]
            rows.append((ident, _tags(item.get("TagSet"), str(path))))
        return rows
    raise ListingError(f"{path}: neither ResourceTagMappingList nor NetworkInterfaces present")


def leftovers(rows: list[Row], environment: str, cluster: str) -> list[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for ident, tags in rows:
        if tags.get(BOOTSTRAP_TAG[0]) == BOOTSTRAP_TAG[1]:
            continue
        # A network interface made by the VPC CNI carries neither of the two tags above (bug 5.14);
        # its owner tag and the cluster's name tag name it.
        owner_key, owner_value = CNI_OWNER_TAG
        cni = tags.get(owner_key) == owner_value and tags.get(CNI_CLUSTER_TAG) == cluster
        if tags.get(ENV_TAG) == environment or tags.get(CLUSTER_TAG) == cluster or cni:
            found.add((classify(ident), ident))
    return sorted(found)


STATUSES = {"gone", "found", "error", "unconfirmed"}


def read_confirmations(path: Path) -> dict[str, str]:
    """`<id>\t<status>` per line; an unreadable file or unknown status is untrustworthy."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ListingError(f"{path}: unreadable confirmations ({error})") from error
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        ident, sep, status = line.partition("\t")
        if not sep or status not in STATUSES:
            raise ListingError(f"{path}: malformed confirmation line {line!r}")
        statuses[ident] = status
    return statuses


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="env-down leftover check")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--environment", default="eks")
    parser.add_argument("--cluster", default="ticketscope-env")
    parser.add_argument("--list", action="store_true", dest="list_only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--candidates", action="store_true")
    parser.add_argument("--confirmations", type=Path)
    args = parser.parse_args(argv)

    rows: list[Row] = []
    if args.dry_run:
        rows.append((DRY_RUN_ARN, {ENV_TAG: args.environment}))
    else:
        if not args.files:
            print("leftover-check: no listing given; nothing can be called clean", file=sys.stderr)
            return 2
        try:
            for path in args.files:
                rows.extend(read_listing(path))
        except ListingError as error:
            print(f"leftover-check: FAIL, {error}", file=sys.stderr)
            return 2

    found = leftovers(rows, args.environment, args.cluster)
    if args.candidates:
        for kind, ident in found:
            print(f"{kind}\t{ident}")
        return 0
    if args.list_only:
        for kind, ident in found:
            print(f"found {kind} {ident}")
        print(f"leftover-check: {len(found)} tagged resource(s) for environment={args.environment}")
        return 0
    statuses: dict[str, str] = {}
    if args.confirmations is not None:
        try:
            statuses = read_confirmations(args.confirmations)
        except ListingError as error:
            print(f"leftover-check: FAIL, {error}", file=sys.stderr)
            return 2
        kept: list[tuple[str, str]] = []
        for kind, ident in found:
            if statuses.get(ident) == "gone":
                print(f"GONE {kind} {ident} (tagging API lag)")
            else:
                kept.append((kind, ident))
        found = kept
    for kind, ident in found:
        status = statuses.get(ident, "unconfirmed") if args.confirmations is not None else "found"
        note = "" if status == "found" else f" ({status})"
        print(f"LEFTOVER {kind} {ident}{note}")
    if found:
        print(
            f"leftover-check: FAIL, {len(found)} tagged resource(s) outside Terraform state",
            file=sys.stderr,
        )
        return 1
    print(f"leftover-check: clean, nothing tagged environment={args.environment} remains")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
