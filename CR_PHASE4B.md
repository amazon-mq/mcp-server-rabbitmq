# Phase 4B: Blue-Green Migration Tools

**Branch:** `feat/phase4b-blue-green`
**Base:** `feat/phase4a-multi-broker` (PR #20)
**Files changed:** 4 (+334 lines, 1 new file)

## Summary

Adds definition transformation engine and cross-broker migration tools for blue-green deployments. Directly supports CMQ→QQ migration workflows (TeleTracking, JPMC use cases).

## New File: `transforms.py`

Definition transformation engine matching rabbitmqadmin-ng capabilities:

| Transform | Description | Use Case |
|-----------|-------------|----------|
| `strip_cmq_keys` | Remove `ha-mode`, `ha-params`, `ha-sync-mode` etc. from policies | CMQ → QQ migration |
| `drop_empty_policies` | Remove policies with empty definitions | Pair with strip_cmq_keys |
| `convert_classic_to_quorum` | Change `x-queue-type: classic` → `quorum` in queue args | Modernize queue types |
| `obfuscate_credentials` | Replace usernames/passwords with dummy values | Share definitions for debugging |
| `exclude_users` | Remove users section | Target has own user management |
| `exclude_permissions` | Remove permissions/topic_permissions | Same |

Transforms are chainable via `apply_transforms(definitions, ["strip_cmq_keys", "drop_empty_policies"])`.

## New Tools

### Read-only (2)

| Tool | Description |
|------|-------------|
| `compare_definitions` | Cross-broker topology diff. Compares queues, exchanges, bindings, policies, vhosts between two connected brokers. Returns missing/extra items per section. |
| `check_migration_readiness` | Pre-flight check: both brokers connected, no alarms on either side, topology comparison. Returns go/no-go with detailed check results. |

### Mutative (4)

| Tool | Description |
|------|-------------|
| `export_definitions` | Export from active broker with optional transforms. Wraps `GET /api/definitions`. |
| `import_definitions` | Import to active broker. Wraps `POST /api/definitions` (merge behavior). |
| `migrate_definitions` | Export from source → transform → import to target in one call. The core blue-green primitive. |
| `setup_federation` | Create federation upstream + blanket policy on active broker. **Checks federation plugin is enabled first** — returns error with instructions if not. |

## Blue-Green Workflow (enabled by this PR)

```
1. initialize_connection(hostname="old-broker", alias="blue")
2. initialize_connection(hostname="new-broker", alias="green")
3. check_migration_readiness(source_alias="blue", target_alias="green")
4. migrate_definitions(source="blue", target="green", transforms=["strip_cmq_keys", "drop_empty_policies"])
5. compare_definitions(source_alias="blue", target_alias="green")  # verify
6. select("green") → setup_federation(upstream_uri="amqp://old-broker")
7. Monitor drain, cut over DNS, cleanup
```

## Tool Count After This PR

| Tier | Phase 4A | Phase 4B | Delta |
|------|----------|----------|-------|
| Critical | 5 | 5 | — |
| Read-only | 21 | 23 | +2 |
| Mutative | 17 | 21 | +4 |
| **Total** | **43** | **49** | **+6** |

## Testing

- All 44 existing tests pass
- `ruff check` clean
- Transforms are pure functions operating on dicts — easy to unit test (deferred to Phase 6 integration tests)

## Risk

Medium. Migration tools are powerful — `migrate_definitions` imports topology to a target broker, `setup_federation` creates upstream links. All gated behind `--allow-mutative-tools`. The `check_migration_readiness` pre-flight tool is designed to be called first as a safety check.
