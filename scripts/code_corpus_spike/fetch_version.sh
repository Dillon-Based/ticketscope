#!/bin/bash
# Download each version's client jar and mappings from Mojang with curl, verifying SHA-1.
# usage: fetch_version.sh <manifest.json> <out dir> <version id>...
set -euo pipefail
manifest="$1"; out="$2"; shift 2
for vid in "$@"; do
  dest="$out/$vid"; mkdir -p "$dest"
  url=$(python3 -I -c 'import json,sys; print(next(v["url"] for v in json.load(open(sys.argv[1]))["versions"] if v["id"]==sys.argv[2]))' "$manifest" "$vid")
  curl -sS --retry 3 --max-time 60 -o "$dest/version.json" "$url"
  for pair in client:client.jar client_mappings:client.txt; do
    key="${pair%%:*}"; name="${pair##*:}"
    [ -s "$dest/$name" ] && continue
    read -r dl sha < <(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1]))["downloads"][sys.argv[2]]; print(d["url"], d["sha1"])' "$dest/version.json" "$key")
    curl -sS --retry 3 --max-time 300 -o "$dest/$name" "$dl"
    got=$(shasum -a 1 "$dest/$name" | cut -d' ' -f1)
    [ "$got" = "$sha" ] || { echo "sha1 mismatch $vid $name" >&2; exit 1; }
    echo "$vid $name $(wc -c < "$dest/$name") bytes sha1 ok"
  done
done
