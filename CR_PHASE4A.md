# Phase 4A: Multi-Broker Connection Registry

**Branch:** `feat/phase4a-multi-broker`
**Base:** `feat/phase3-core-crud` (PR #19)
**Files changed:** 2 (module.py, test_module.py) | +114 / -149 lines (net reduction)

## Summary

Replaces the single-connection model (`self.rmq` / `self.rmq_admin`) with a broker registry that supports multiple simultaneous connections. This is the foundation for blue-green migration (Phase 4B).

## Problem

The README claimed "Connect to multiple brokers in one session" but calling `initialize_connection` a second time silently overwrote the first connection. There was no way to manage multiple brokers.

## Solution

### New data model

```python
self.brokers: dict[str, dict] = {}      # alias -> {rmq, rmq_admin, hostname}
self.active_alias: str | None = None     # currently active broker
```

### Helper methods

```python
def _get_admin(self) -> RabbitMQAdmin    # returns active broker's admin client
def _get_rmq(self) -> RabbitMQConnection # returns active broker's AMQP connection
```

Both raise `AssertionError` if no broker is active — same error behavior as before.

### New tools

| Tool | Tier | Description |
|------|------|-------------|
| `rabbitmq_broker_select` | Critical | Switch active broker by alias |
| `rabbitmq_broker_list_registered_brokers` | Critical | List all connections with active indicator |

### Modified tools

| Tool | Change |
|------|--------|
| `initialize_connection` | Added optional `alias` param (default: hostname). Registers in broker dict, sets as active. |
| `initialize_connection_with_oauth` | Same |

### All 41 existing tools

Updated to use `self._get_admin()` / `self._get_rmq()` instead of direct `self.rmq_admin` / `self.rmq`. Removed 38 inline guard blocks (replaced by guards in helper methods).

## Backward Compatibility

Single-broker usage is unchanged:
1. Call `initialize_connection(hostname="my-broker", ...)` — registers as alias "my-broker", sets active
2. Call any tool — works exactly as before

Multi-broker usage:
1. Call `initialize_connection(hostname="broker-a", alias="blue", ...)`
2. Call `initialize_connection(hostname="broker-b", alias="green", ...)`
3. `green` is now active (last connected)
4. Call `rabbitmq_broker_select(alias="blue")` to switch
5. All subsequent tools target `blue`

## Testing

- All 44 tests pass (updated test_module.py for new data model)
- `ruff check` clean

## Risk

Low. The external tool API is backward compatible. Internal refactor replaces direct attribute access with helper methods. The only breaking change is for code that directly accessed `module.rmq` or `module.rmq_admin` — but these are private implementation details, not part of the MCP tool interface.
