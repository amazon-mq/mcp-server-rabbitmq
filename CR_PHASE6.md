# Phase 6: Developer Experience (Scoped Down)

**Branch:** `feat/phase6-dx`
**Base:** `feat/phase5-health-ops` (PR #22)
**Files changed:** 3 (+32 lines, 1 new file)

## Summary

Adds local development infrastructure and management port CLI configuration. Scoped down from original plan — integration tests, MCP Resources, and server instructions deferred.

## Changes

### `docker-compose.yml` (new)

Local RabbitMQ 4 broker with management plugin:
- `rabbitmq:4-management` image
- Ports: 5672 (AMQP), 15672 (Management HTTP API)
- Default credentials: guest/guest
- Healthcheck via `rabbitmq-diagnostics ping`
- Persistent volume for data

Usage:
```bash
docker compose up -d
# Connect with: hostname=localhost, port=5672, management port=15672, use_tls=false
```

### `--management-port` CLI argument

```bash
amq-mcp-server-rabbitmq --management-port 15672 --allow-mutative-tools
```

Sets the default management API port for all broker connections. When not specified, defaults to 443 (TLS) or 15672 (non-TLS). Eliminates the need to configure port per-connection for local development.

## Deferred Items

| Item | Reason |
|------|--------|
| Integration tests | Valuable but not blocking. Can be added incrementally. |
| MCP Resources | `get_guideline` tool works. Resources are more idiomatic but not blocking. |
| Server instructions | Nice-to-have for agent guidance. |

## Testing

- All 44 tests pass, `ruff check` clean
