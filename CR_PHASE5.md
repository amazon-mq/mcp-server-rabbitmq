# Phase 5: Extended Health Checks & Ops Tools

**Branch:** `feat/phase5-health-ops`
**Base:** `feat/phase4b-blue-green` (PR #21)
**Files changed:** 3 | +141 lines

## Summary

Adds 8 tools covering the remaining RabbitMQ health check endpoints and operational utilities.

## New Read-Only Tools (7)

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `check_local_alarms` | `GET /health/checks/local-alarms` | Local alarm status |
| `check_certificate_expiration` | `GET /health/checks/certificate-expiration/{within}/{unit}` | TLS cert expiry (configurable: 30 days default) |
| `check_protocol_listener` | `GET /health/checks/protocol-listener/{protocol}` | Verify listeners (amqp091, amqp10, mqtt, stomp, etc.) |
| `check_virtual_hosts` | `GET /health/checks/virtual-hosts` | Health of all vhosts |
| `list_feature_flags` | `GET /feature-flags` | All feature flags and status |
| `list_deprecated_features` | `GET /deprecated-features/used` | Deprecated features in use (upgrade planning) |
| `whoami` | `GET /whoami` | Current authenticated user |

## New Mutative Tools (1)

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `rebalance_queues` | `POST /rebalance/queues` | Rebalance queue leaders across cluster nodes |

## Tool Count: 57 total (30 read-only, 22 mutative, 5 critical)

## Testing

- All 44 tests pass, `ruff check` clean

## Risk

Low. All additive, no existing behavior changed. Health checks are read-only. Rebalance is gated behind `--allow-mutative-tools`.
