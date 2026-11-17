#!/usr/bin/env python3
"""Mask a real `aws resourcegroupstaggingapi get-resources` list for committing as a fixture.

    python3 scripts/mask_aws_list.py /tmp/up.raw.json tests/fixtures/aws/up.json

Keeps the service, resource type, tag keys and the shape; replaces the account id, every
resource id and any id-bearing tag value with stable placeholders (the same real value always
maps to the same placeholder, so references between resources survive). Nothing about the
person or the account is written.
"""

import json
import re
import sys
from pathlib import Path

ACCOUNT = re.compile(r"\b\d{12}\b")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
# Tag values that carry cluster-generated ids or names; the rest (environment, project, stack,
# the cluster name) are kept because they are what the leftover check filters on.
MASKED_TAG_KEYS = {
    "CSIVolumeName",
    "kubernetes.io/created-for/pv/name",
    "kubernetes.io/created-for/pvc/name",
    "kubernetes.io/created-for/pvc/namespace",
    "elbv2.k8s.aws/resource",
    "gateway.k8s.aws.alb/resource",
    "gateway.k8s.aws.alb/stack",
}


class Masker:
    def __init__(self) -> None:
        self._ids: dict[str, str] = {}

    def id(self, real: str, kind: str) -> str:
        key = f"{kind}:{real}"
        if key not in self._ids:
            self._ids[key] = f"{kind}-{len(self._ids) + 1:03d}"
        return self._ids[key]

    def arn(self, arn: str) -> str:
        parts = arn.split(":", 5)
        if len(parts) < 6:
            return ACCOUNT.sub("000000000000", arn)
        parts[4] = "000000000000" if parts[4] else ""
        resource = parts[5]
        kind, sep, rest = resource.partition("/")
        if not sep:
            kind, sep, rest = resource.partition(":")
        parts[5] = f"{kind}{sep}{self.id(rest, kind)}" if rest else resource
        return ":".join(parts)


def mask(doc: dict) -> dict:
    masker = Masker()
    rows = []
    for row in doc["ResourceTagMappingList"]:
        tags = []
        for tag in row.get("Tags", []):
            value = tag["Value"]
            if tag["Key"] in MASKED_TAG_KEYS:
                value = masker.id(value, "value")
            value = UUID.sub(lambda m: masker.id(m.group(0), "uuid"), value)
            value = ACCOUNT.sub("000000000000", value)
            tags.append({"Key": tag["Key"], "Value": value})
        tags.sort(key=lambda t: t["Key"])
        rows.append({"ResourceARN": masker.arn(row["ResourceARN"]), "Tags": tags})
    rows.sort(key=lambda r: r["ResourceARN"])
    return {"ResourceTagMappingList": rows}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    masked = mask(json.loads(source.read_text(encoding="utf-8")))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(masked, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target} ({len(masked['ResourceTagMappingList'])} resources)")


if __name__ == "__main__":
    main()
