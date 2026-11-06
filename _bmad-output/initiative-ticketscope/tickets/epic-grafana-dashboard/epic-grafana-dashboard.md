---
type: epic
title: "One Grafana dashboard shows the service's telemetry"
parent: initiative-ticketscope
covers: [R9]
sources: []
companions: []
after: []
refined: false
risk: low
---

# One Grafana dashboard shows the service's telemetry

## Description

One Grafana dashboard, deployed with the chart on epic 5's live environment, shows request rate, retrieval latency for each of epic 3's modes, epic 4's MCP tool calls, and errors. Its metrics are derived from the spans that epics 1, 3 and 4 emit.

## Outcome

An operator sees ticketscope's health and retrieval latency by mode at a glance on the live environment (initiative R9).

## Done when

- The dashboard is provisioned by the chart, with no manual import (R9).
- On the live environment it shows request rate, latency per retrieval mode, MCP tool calls and errors (R9).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- This is the first epic on the brief's cut list. Only one dashboard is in scope.

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R9)

## Notes

- Waits on epic-hybrid-retrieval because: latency by mode needs all three modes.
- Waits on epic-mcp-server because: it needs the MCP tool-call telemetry.
- Waits on epic-eks-environment because: it needs the live environment and its chart values.
- Waits on epic-mcp-oauth because: both edit the live ingress and chart values.
