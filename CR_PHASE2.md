# Phase 2: Expose Already-Implemented but Unregistered Tools

**Branch:** `feat/phase2-expose-existing`
**Base:** `fix/phase1-bug-fixes-code-quality` (PR #17)
**Files changed:** 2 (handlers.py, module.py) | +57 lines

## Summary

Four functions existed in the codebase but were never registered as MCP tools — making them completely inaccessible to agents. This PR wires them up.

## New Tools

### Read-only (always available)

| Tool | Handler | API | Description |
|------|---------|-----|-------------|
| `rabbitmq_broker_get_bindings` | `handle_get_bindings` | `GET /api/bindings/{vhost}` | Get bindings, optionally filtered by queue or exchange. `admin.py` had the full implementation including queue/exchange filtering — never exposed. |
| `rabbitmq_broker_get_node_information` | `handle_get_node_information` | `GET /api/nodes/{name}` | Get detailed node info (memory, disk, uptime, runtime). Complements existing `get_cluster_nodes_info` which returns a summary list. |

### Mutative (requires `--allow-mutative-tools`)

| Tool | Handler | Protocol | Description |
|------|---------|----------|-------------|
| `rabbitmq_broker_enqueue` | `handle_enqueue` | AMQP | Publish a message to a specific queue. Declares queue if it doesn't exist. Handler existed in `handlers.py` since initial commit but was never imported or registered. |
| `rabbitmq_broker_fanout` | `handle_fanout` | AMQP | Publish a message to a fanout exchange. Declares exchange if it doesn't exist. Same situation — existed but never wired up. |

## Tool Count After This PR

| Tier | Before | After |
|------|--------|-------|
| Critical | 3 | 3 |
| Read-only | 14 | 16 (+2) |
| Mutative | 4 | 6 (+2) |
| **Total** | **21** | **25** |

## Testing

- All 44 existing tests pass
- `ruff check` clean
- Note: enqueue/fanout require a live AMQP connection to test end-to-end (no integration test suite yet — planned for Phase 6)

## Risk

Low. No existing behavior changed. Four new tools added, all backed by pre-existing implementations.
