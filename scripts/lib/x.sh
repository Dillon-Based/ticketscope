# shellcheck shell=bash
# `x <command...>`: echoes the command to stderr, then runs it. The drills (restore-drill.sh,
# failure-drill.sh) keep their commands in the record this way. Sourced; never run on its own.
x() { printf '+ %s\n' "$*" >&2; "$@"; }
