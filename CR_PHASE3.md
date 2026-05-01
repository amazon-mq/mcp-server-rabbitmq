# Phase 3: Core CRUD Tools

**Branch:** `feat/phase3-core-crud`
**Base:** `feat/phase2-expose-existing` (PR #18)
**Files changed:** 3 (admin.py, handlers.py, module.py) | +506 lines

## Summary

Adds 16 new MCP tools covering the most significant gaps in RabbitMQ Management HTTP API coverage. Before this PR, the server could delete queues/exchanges but not create them, had no policy management, no message inspection, and no vhost/permission management.

## New Read-Only Tools (5)

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `rabbitmq_broker_list_policies` | `GET /api/policies/{vhost}` | List all policies in a vhost |
| `rabbitmq_broker_get_policy` | `GET /api/policies/{vhost}/{name}` | Get a specific policy |
| `rabbitmq_broker_get_messages` | `POST /api/queues/{vhost}/{name}/get` | Peek at messages without consuming (requeues by default) |
| `rabbitmq_broker_list_channels` | `GET /api/channels` | List all open channels |
| `rabbitmq_broker_get_permissions` | `GET /api/permissions/{vhost}/{user}` | Get user permissions in a vhost |

## New Mutative Tools (11)

| Tool | API Endpoint | Description |
|------|-------------|-------------|
| `rabbitmq_broker_create_queue` | `PUT /api/queues/{vhost}/{name}` | Create queue (quorum default, supports classic/stream) |
| `rabbitmq_broker_create_exchange` | `PUT /api/exchanges/{vhost}/{name}` | Create exchange (direct/fanout/topic/headers) |
| `rabbitmq_broker_create_binding` | `POST /api/bindings/{vhost}/e/{ex}/q/{q}` | Bind exchange to queue with routing key |
| `rabbitmq_broker_delete_binding` | `DELETE /api/bindings/{vhost}/e/{ex}/q/{q}/{props}` | Delete a binding |
| `rabbitmq_broker_create_policy` | `PUT /api/policies/{vhost}/{name}` | Create/update policy (HA, TTL, max-length, etc.) |
| `rabbitmq_broker_delete_policy` | `DELETE /api/policies/{vhost}/{name}` | Delete a policy |
| `rabbitmq_broker_publish_message` | `POST /api/exchanges/{vhost}/{name}/publish` | Publish via HTTP API (diagnostics) |
| `rabbitmq_broker_close_connection` | `DELETE /api/connections/{name}` | Close a connection |
| `rabbitmq_broker_create_vhost` | `PUT /api/vhosts/{name}` | Create a virtual host |
| `rabbitmq_broker_delete_vhost` | `DELETE /api/vhosts/{name}` | Delete a vhost and all its resources |
| `rabbitmq_broker_set_permissions` | `PUT /api/permissions/{vhost}/{user}` | Set configure/write/read permissions |

## Tool Count After This PR

| Tier | Phase 2 | Phase 3 | Delta |
|------|---------|---------|-------|
| Critical | 3 | 3 | — |
| Read-only | 16 | 21 | +5 |
| Mutative | 6 | 17 | +11 |
| **Total** | **25** | **41** | **+16** |

## Design Decisions

1. **`create_queue` defaults to quorum type** — quorum queues are the recommended type for RabbitMQ 3.13+. Classic queues are still supported via the `queue_type` parameter.

2. **`get_messages` defaults to `ack_requeue_true`** — this is a peek operation by default. Messages are not consumed. The `ackmode` parameter allows consuming if explicitly requested.

3. **`publish_message` is via HTTP API, not AMQP** — intended for diagnostics and testing. The existing `enqueue`/`fanout` tools use AMQP for production publishing.

4. **`delete_vhost` has a WARNING in its docstring** — it deletes all queues, exchanges, bindings, and permissions in the vhost. Agents should confirm before calling.

## Testing

- All 44 existing tests pass
- `ruff check` clean
- New tools follow the same pattern as existing ones — admin method → handler → tool registration
- Integration testing requires a live broker (planned for Phase 6)

## Risk

Low-medium. All new tools are additive — no existing behavior changed. Mutative tools are gated behind `--allow-mutative-tools`. The `delete_vhost` tool is the highest-risk addition (destructive), but it's clearly documented and gated.
