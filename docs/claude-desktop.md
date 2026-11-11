# Claude Desktop through a tunnel

Claude Desktop calls `search_similar_issues` on the kind cluster's `/mcp` through a tunnel with a
fixed public hostname. The tunnel runs on your machine, never in CI, and no credential is
committed.

## Choosing the tunnel

ngrok's free static domain is the first choice; Tailscale Funnel is the fallback. Before choosing
ngrok, curl `https://<host>/mcp` from outside with a non-browser client and confirm:

- no interstitial page comes back;
- a streamed (SSE) response arrives intact, not buffered;
- ngrok's free bandwidth limit covers a demo.

If any check fails, use Tailscale Funnel. Record the choice and why in the story 4.2 plan.

## Run it

```bash
export TUNNEL_HOSTNAME=<reserved-host>      # the one environment value
scripts/kind-up.sh                           # Gateway listener, /mcp route and allowed hosts admit it
export NGROK_AUTHTOKEN=<your token>          # from your environment, never committed
scripts/tunnel.sh                            # TUNNEL_PROVIDER=tailscale for Funnel
```

The tunnel stops when the script exits, and the hostname then no longer reaches the cluster. The
tunnel host reaches only `/mcp`; `/v1/search` and `/` answer 404.

## Add the connector

In Claude Desktop: Settings, Connectors, Add custom connector. Enter `https://<host>/mcp` and leave
authentication empty (epic 6 adds it). Ask a triage question; Claude calls `search_similar_issues`
and answers citing the returned issues.

## Capture the requests

Save the session's `initialize`, `notifications/initialized`, `tools/list` and `tools/call`
requests, with the protocol version and headers and no credentials, under `tests/mcp/captured/`.
`mcp-e2e.yml` replays them on every PR. Later stories do not edit them.
