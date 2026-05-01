# Integration Test Suite

**Branch:** `feat/integration-tests`
**Base:** `feat/phase6-dx` (PR #23)
**Files changed:** 4 (+330 lines, 3 new files)

## Summary

38 integration tests covering all Phase 3-5 tools. Tests run against a local RabbitMQ broker via docker-compose and skip gracefully when no broker is available.

## Test Coverage

| Category | Tests | What's Covered |
|----------|-------|----------------|
| Health | 7 | whoami, alarms, quorum critical, local alarms, vhosts health, feature flags, deprecated features |
| Cluster | 2 | list nodes, get node info |
| Queues | 6 | create, list, get info, publish+peek, purge, delete |
| Exchanges | 4 | create, list, get info, delete |
| Bindings | 2 | create+list, delete |
| Policies | 4 | create, list, get, delete |
| Vhosts | 3 | create, set+get permissions, delete |
| Connections | 5 | list connections, consumers, channels, users, shovels |
| Definitions | 4 | get, export with transforms, compare identical |
| Transforms | 2 | strip_cmq+drop_empty, convert_classic_to_quorum (pure, no broker needed) |

## Running

```bash
# Start broker
docker compose up -d

# Run integration tests
pytest src/tests/integration/ -v

# Run unit tests only (no broker needed)
pytest src/tests/ --ignore=src/tests/integration
```

## Other Changes

- Fixed `pyproject.toml` testpaths: `tests` → `src/tests`
- Added `integration` pytest marker
- Version bumped to 3.0.0 in pyproject.toml
