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

One Grafana dashboard is provisioned by the platform release on epic 5's live environment. It shows:

- request rate
- retrieval latency for each of epic 3's modes
- epic 4's MCP tool calls
- errors

Its metrics come from the spans that epics 1, 3 and 4 emit, through the collector's spanmetrics connector into Prometheus, which this epic adds.

## Outcome

An operator sees ticketscope's health and retrieval latency by mode at a glance on the live environment (initiative R9).

## Done when

- The dashboard is provisioned by the platform release, with no manual import (R9).
- On the live environment it shows request rate, latency per retrieval mode, MCP tool calls and errors. Every panel is derived from spans, and job spans are excluded (R9).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- This is the first epic on the brief's cut list. Only one dashboard is in scope. Tempo and Grafana themselves ship in epic-search-baseline, so a cut keeps trace viewing.
- Out: hand-written application metrics; the apps emit traces only.

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R9)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-3, AD-10, AD-11, AD-13, AD-14, AD-23, AD-25

## Notes

- Waits on epic-hybrid-retrieval because: latency by mode needs all three modes.
- Waits on epic-mcp-server because: it needs the MCP tool-call spans.
- Waits on epic-eks-environment because: it needs the live environment and its values file.
- Waits on epic-mcp-oauth because: both edit the EKS values file, and this order follows the cut order, so a cut drops this epic first.
- Decision: Adopted the architecture spine. Metrics come from spanmetrics into Prometheus, and the reason for the wait on epic-mcp-oauth was restated now that ingress is a fixed route table (user, 2026-11-05).
