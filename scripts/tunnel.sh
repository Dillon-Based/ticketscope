#!/usr/bin/env bash
# Exposes the kind Gateway on the tunnel's fixed public hostname, for Claude Desktop.
# Runs on a person's machine, never in CI. The tunnel stops when this script exits.
#
#   TUNNEL_HOSTNAME=<host> scripts/tunnel.sh
#
# Run scripts/kind-up.sh first with the same TUNNEL_HOSTNAME, so the Gateway listener, the
# /mcp route and mcp's allowed hosts admit that host. The tunnel passes the Host header
# through unchanged.
#
# Env:
#   TUNNEL_HOSTNAME   required: the reserved hostname (ngrok static domain, or Tailscale node)
#   TUNNEL_PROVIDER   ngrok (default) or tailscale
#   NGROK_AUTHTOKEN   required for ngrok: read from your environment, never written down
#   GATEWAY_URL       what to expose (default: the port-forward kind-up.sh opens on macOS)
set -euo pipefail

: "${TUNNEL_HOSTNAME:?tunnel: set TUNNEL_HOSTNAME to the reserved hostname}"
PROVIDER="${TUNNEL_PROVIDER:-ngrok}"
GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:18080}"
PID=""

FUNNEL_STARTED=0

cleanup() {
  [[ -n "$PID" ]] && kill "$PID" 2>/dev/null || true
  # Only undo the Funnel this script started.
  if [[ "$FUNNEL_STARTED" == 1 ]]; then
    tailscale funnel --https=443 off >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

case "$PROVIDER" in
  ngrok)
    command -v ngrok >/dev/null || { echo "tunnel: ngrok is required" >&2; exit 1; }
    : "${NGROK_AUTHTOKEN:?tunnel: set NGROK_AUTHTOKEN in your environment}"
    ngrok http "$GATEWAY_URL" --url "https://${TUNNEL_HOSTNAME}" --log=stdout &
    PID=$!
    ;;
  tailscale)
    command -v tailscale >/dev/null || { echo "tunnel: tailscale is required" >&2; exit 1; }
    # Funnel serves on the node's own name: TUNNEL_HOSTNAME must be that exact name (the
    # Gateway, the route and mcp admit only that Host), or Envoy answers 404.
    NODE_NAME="$(tailscale status --json | sed -n 's/.*"DNSName": *"\([^"]*\)\.".*/\1/p' | head -1)"
    if [[ "$NODE_NAME" != "$TUNNEL_HOSTNAME" ]]; then
      echo "tunnel: Funnel serves ${NODE_NAME:-<unknown>}, not ${TUNNEL_HOSTNAME}; set TUNNEL_HOSTNAME to it and re-run kind-up.sh" >&2
      exit 1
    fi
    tailscale funnel --bg "$GATEWAY_URL"
    FUNNEL_STARTED=1
    # BSD sleep (macOS) has no `infinity`.
    while :; do sleep 3600; done &
    PID=$!
    ;;
  *)
    echo "tunnel: TUNNEL_PROVIDER must be ngrok or tailscale" >&2
    exit 1
    ;;
esac

echo "tunnel: https://${TUNNEL_HOSTNAME}/mcp (Ctrl-C to stop)"
wait "$PID"
