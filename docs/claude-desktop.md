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

If any check fails, use Tailscale Funnel. Funnel serves on the node's own `*.ts.net` name, so set
`TUNNEL_HOSTNAME` to exactly that name; `scripts/tunnel.sh` refuses to start when they differ. Record the choice and why in the story 4.2 plan.

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

Claude Desktop speaks the stateless 2026-07-28 protocol, so its handshake is `server/discover`, not
`initialize`. The captured set is `server/discover`, `tools/list`, `tools/call`, `resources/list`
and `prompts/list` in `tests/mcp/captured/`, taken from ngrok's local inspector
(`http://127.0.0.1:4040`) with every header except the proxy's (`Host`, `Content-Length`,
`Accept-Encoding`, `X-Forwarded-*`). Keep all the others: the server rejects a `tools/call` without
its `Mcp-Name` header. `subscriptions/listen` is a long-lived stream and is not replayed.

`mcp-e2e.yml` replays them against `/mcp` with the stand-in tunnel host on every PR. Locally,
set `TICKETSCOPE_TUNNEL_HOST` to the host you gave kind-up.sh. Later stories do not edit the
fixtures; `tests/unit/test_mcp_captured_pin.py` pins their bytes.
