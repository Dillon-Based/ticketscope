#!/usr/bin/env bash
# Story 11 AC-2: break each of the integrated check's five checks on purpose, one at a
# time, and show that the suite fails on exactly that check; restore it, and show the
# suite passes again. Ends with one clean run.
#
#   scripts/fault-inject.sh <out-dir>
#
# Needs the local kind cluster on the pinned snapshot and the variables the integrated
# suite needs (TICKETSCOPE_GATEWAY_URL, TICKETSCOPE_GATEWAY_HOST). Writes one JUnit file
# per run and summary.json to <out-dir>. Every break is restored on exit, even on error.
#
# Breaks (as story 11 names them):
#   schema   a stricter copy of snapshot/schema-v2.json (an extra required field)
#   kind     one issue's kind NULLed via SQL (NOT NULL dropped for the duration)
#   golden   the vague entry's expected number swapped in eval/golden-queries.json
#   tempo    Tempo scaled to 0
#   backup   the backup ObjectStore pointed at a missing bucket
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <out-dir>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
NS="${TICKETSCOPE_NAMESPACE:-ticketscope}"
PLATFORM_NS="${TICKETSCOPE_PLATFORM_NAMESPACE:-platform}"
CLUSTER="${TICKETSCOPE_CLUSTER_NAME:-ticketscope-db}"
OBJECTSTORE="${TICKETSCOPE_OBJECTSTORE:-ticketscope-backup}"
BACKUP_DIR="$(mktemp -d)"

log() { echo "[fault-inject] $*" >&2; }

primary() {
  kubectl -n "$NS" get pod -l "cnpg.io/cluster=${CLUSTER},cnpg.io/instanceRole=primary" \
    -o 'jsonpath={.items[0].metadata.name}'
}
sql() { kubectl -n "$NS" exec "$(primary)" -c postgres -- psql -d app -tAc "$1"; }

# --- breaks and restores ----------------------------------------------------------------

KIND_NUMBER=""
KIND_VALUE=""
DEST=""

break_schema() {
  cp snapshot/schema-v2.json "$BACKUP_DIR/schema-v2.json"
  python3 - <<'EOF'
import json, pathlib
p = pathlib.Path("snapshot/schema-v2.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["required"] = [*d["required"], "fault_injected_field"]
p.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
EOF
}
restore_schema() { cp "$BACKUP_DIR/schema-v2.json" snapshot/schema-v2.json; }

break_kind() {
  KIND_NUMBER="$(sql "SELECT min(number) FROM issue" | tr -d '[:space:]')"
  KIND_VALUE="$(sql "SELECT kind FROM issue WHERE number = ${KIND_NUMBER}" | tr -d '[:space:]')"
  sql "ALTER TABLE issue ALTER COLUMN kind DROP NOT NULL" >/dev/null
  sql "UPDATE issue SET kind = NULL WHERE number = ${KIND_NUMBER}" >/dev/null
  log "issue ${KIND_NUMBER}: kind ${KIND_VALUE} -> NULL"
}
restore_kind() {
  [[ -n "$KIND_NUMBER" ]] || return 0
  sql "UPDATE issue SET kind = '${KIND_VALUE}' WHERE number = ${KIND_NUMBER}" >/dev/null
  sql "ALTER TABLE issue ALTER COLUMN kind SET NOT NULL" >/dev/null
  KIND_NUMBER=""
}

break_golden() {
  cp eval/golden-queries.json "$BACKUP_DIR/golden-queries.json"
  python3 - <<'EOF'
import json, pathlib
p = pathlib.Path("eval/golden-queries.json")
d = json.loads(p.read_text(encoding="utf-8"))
vague = next(q for q in d["queries"] if q["id"] == "vague")
# Swap in the other entry's expected issue: a real loaded issue, never the vague twin.
other = next(q for q in d["queries"] if q["id"] != "vague")
vague["expected_issue"] = dict(other["expected_issue"])
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
EOF
}
restore_golden() { cp "$BACKUP_DIR/golden-queries.json" eval/golden-queries.json; }

break_tempo() { kubectl -n "$PLATFORM_NS" scale statefulset/tempo --replicas=0 >/dev/null; }
restore_tempo() {
  kubectl -n "$PLATFORM_NS" scale statefulset/tempo --replicas=1 >/dev/null
  kubectl -n "$PLATFORM_NS" rollout status statefulset/tempo --timeout=300s >&2
}

break_backup() {
  DEST="$(kubectl -n "$NS" get objectstores.barmancloud.cnpg.io "$OBJECTSTORE" \
    -o 'jsonpath={.spec.configuration.destinationPath}')"
  kubectl -n "$NS" patch objectstores.barmancloud.cnpg.io "$OBJECTSTORE" --type merge \
    -p '{"spec":{"configuration":{"destinationPath":"s3://fault-injected-missing-bucket/"}}}' >/dev/null
  log "ObjectStore ${OBJECTSTORE}: ${DEST} -> s3://fault-injected-missing-bucket/"
}
restore_backup() {
  [[ -n "$DEST" ]] || return 0
  kubectl -n "$NS" patch objectstores.barmancloud.cnpg.io "$OBJECTSTORE" --type merge \
    -p "{\"spec\":{\"configuration\":{\"destinationPath\":\"${DEST}\"}}}" >/dev/null
  DEST=""
}

restore_all() {
  set +e
  [[ -f "$BACKUP_DIR/schema-v2.json" ]] && restore_schema
  [[ -f "$BACKUP_DIR/golden-queries.json" ]] && restore_golden
  restore_kind
  restore_backup
  if [[ "$(kubectl -n "$PLATFORM_NS" get statefulset/tempo -o 'jsonpath={.spec.replicas}')" == "0" ]]; then
    restore_tempo
  fi
  rm -rf "$BACKUP_DIR"
}
trap restore_all EXIT

# --- runs -------------------------------------------------------------------------------

target() {  # <check>: the integrated test it must fail (bash 3 has no associative arrays)
  case "$1" in
    schema) echo test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2 ;;
    kind) echo test_every_loaded_issue_has_a_valid_kind_and_outcome ;;
    golden) echo test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page ;;
    tempo) echo test_one_search_reaches_tempo_as_the_ad10_tree ;;
    backup) echo test_an_on_demand_backup_completes_to_seaweedfs ;;
  esac
}

run_suite() {  # <name>: run the integrated suite once; prints failing test names
  uv run pytest -m kind tests/integrated -q -p no:randomly \
    --junitxml="$OUT/$1.xml" >"$OUT/$1.log" 2>&1 || true
  python3 - "$OUT/$1.xml" <<'EOF'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).getroot().iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print(case.get("name"))
EOF
}

results=()
record() {  # <check> <phase> <ok> <detail>
  results+=("$(printf '{"check":"%s","phase":"%s","ok":%s,"detail":"%s"}' "$1" "$2" "$3" "$4")")
}

overall=0
for check in schema kind golden tempo backup; do
  log "== ${check}: break"
  "break_${check}"
  failing="$(run_suite "${check}-broken" | sort | tr '\n' ' ' | sed 's/ $//')"
  if [[ "$failing" == "$(target "$check")" ]]; then
    record "$check" broken true "only ${failing} failed"
    log "${check}: suite failed on exactly ${failing}"
  else
    record "$check" broken false "failing: ${failing:-none}"
    log "${check}: expected only $(target "$check") to fail, got: ${failing:-none}"
    overall=1
  fi
  log "== ${check}: restore"
  "restore_${check}"
  failing="$(run_suite "${check}-restored")"
  if [[ -z "$failing" ]]; then
    record "$check" restored true "all five passed"
  else
    record "$check" restored false "failing: $(echo "$failing" | tr '\n' ' ')"
    overall=1
  fi
done

{
  echo '{"results": ['
  (IFS=,; echo "${results[*]}")
  echo "], \"ok\": $([[ $overall -eq 0 ]] && echo true || echo false)}"
} >"$OUT/summary.json"
log "summary: $OUT/summary.json"
exit "$overall"
