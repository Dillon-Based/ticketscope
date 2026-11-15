#!/bin/bash
# Remap one version's client jar to Mojang's names, then decompile it.
# usage: decompile.sh <root> <version id>
# Needs <root>/tools/art.jar (NeoForged AutoRenamingTool, -all jar) and
# <root>/tools/vineflower.jar, and <root>/mc/<version id>/ from fetch_version.sh.
# Everything it writes is Mojang code: keep <root> outside the repository.
set -euo pipefail
root="$1"; vid="$2"
java="${JAVA:-java}"  # any JDK 17+
dir="$root/mc/$vid"
[ -d "$dir/src" ] && { echo "$vid already decompiled"; exit 0; }
t0=$(date +%s)
"$java" -jar "$root/tools/art.jar" --input "$dir/client.jar" --output "$dir/named.jar" \
  --map "$dir/client.txt" --reverse > "$dir/remap.log" 2>&1
t1=$(date +%s)
mkdir -p "$dir/src"
"$java" -Xmx6g -jar "$root/tools/vineflower.jar" --only=net/minecraft --only=com/mojang \
  -log=WARN "$dir/named.jar" "$dir/src" > "$dir/decompile.log" 2>&1
t2=$(date +%s)
echo "$vid remap $((t1 - t0))s decompile $((t2 - t1))s java files $(find "$dir/src" -name '*.java' | wc -l | tr -d ' ') size $(du -sh "$dir/src" | cut -f1)"
