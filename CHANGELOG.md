# Changelog

## 4.0.0-rc.1 (2026-05-29)

### Breaking Changes
- New `--v4` flag activates consolidated tool layout (61 tools -> 28)
- Tool names changed (see Migration Guide below)
- Default mode unchanged (no --v4 = v3 behavior)

### New Features
- Dynamic tool loading via `--tool-groups` (core, read, mutative, migration, observability, health)
- Enum-based action dispatchers reduce context window usage
- `--v1-compat` flag provides backward-compatible aliases for v3 tool names

### Bug Fixes
- Fixed `handle_enqueue` declaring queues as non-durable (broke on RabbitMQ 4.x)
- Fixed `handle_fanout` declaring exchanges as non-durable

### Migration Guide (v3 -> v4)

| v3 Tool Name | v4 Equivalent |
|---|---|
| `rabbitmq_broker_initialize_connection` | `connect` |
| `rabbitmq_broker_initialize_connection_with_oauth` | `connect_oauth` |
| `rabbitmq_broker_select` | `broker(action="select")` |
| `rabbitmq_broker_list_registered_brokers` | `broker(action="list")` |
| `rabbitmq_broker_get_guideline` | `get_guideline` |
| `rabbitmq_broker_get_skill` | `get_skill` |
| `rabbitmq_broker_list_queues` | `queues(action="list")` |
| `rabbitmq_broker_get_queue_info` | `queues(action="info")` |
| `rabbitmq_broker_get_messages` | `queues(action="messages")` |
| `rabbitmq_broker_get_bindings` (queue filter) | `queues(action="bindings")` |
| `rabbitmq_broker_list_exchanges` | `exchanges(action="list")` |
| `rabbitmq_broker_get_exchange_info` | `exchanges(action="info")` |
| `rabbitmq_broker_get_bindings` (exchange filter) | `exchanges(action="bindings")` |
| `rabbitmq_broker_list_connections` | `connections(action="list")` |
| `rabbitmq_broker_list_channels` | `connections(action="channels")` |
| `rabbitmq_broker_get_connection_churn` | `connections(action="churn")` |
| `rabbitmq_broker_close_connection` | `connections(action="close")` |
| `rabbitmq_broker_get_cluster_nodes_info` | `cluster(action="nodes")` |
| `rabbitmq_broker_get_node_information` | `cluster(action="node_info")` |
| (new) | `cluster(action="node_memory")` |
| `rabbitmq_broker_rebalance_queues` | `cluster(action="rebalance")` |
| `rabbitmq_broker_list_vhosts` | `entities(action="vhosts")` |
| `rabbitmq_broker_list_users` | `entities(action="users")` |
| `rabbitmq_broker_list_consumers` | `entities(action="consumers")` |
| `rabbitmq_broker_list_policies` | `policies(action="list")` |
| `rabbitmq_broker_get_policy` | `policies(action="get")` |
| `rabbitmq_broker_list_shovels` | `shovels(action="list")` |
| `rabbitmq_broker_get_shovel_info` | `shovels(action="get")` |
| `rabbitmq_broker_get_overview` | `overview(action="summary")` |
| `rabbitmq_broker_get_broker_definition` | `overview(action="definitions")` |
| `rabbitmq_broker_whoami` | `auth(action="whoami")` |
| `rabbitmq_broker_get_permissions` | `auth(action="permissions")` |
| `rabbitmq_broker_set_permissions` | `auth(action="set_permissions")` |
| `rabbitmq_broker_create_queue` | `manage_queue(action="create")` |
| `rabbitmq_broker_delete_queue` | `manage_queue(action="delete")` |
| `rabbitmq_broker_purge_queue` | `manage_queue(action="purge")` |
| `rabbitmq_broker_create_exchange` | `manage_exchange(action="create")` |
| `rabbitmq_broker_delete_exchange` | `manage_exchange(action="delete")` |
| `rabbitmq_broker_create_binding` | `manage_binding(action="create")` |
| `rabbitmq_broker_delete_binding` | `manage_binding(action="delete")` |
| `rabbitmq_broker_create_policy` | `manage_policy(action="create")` |
| `rabbitmq_broker_delete_policy` | `manage_policy(action="delete")` |
| `rabbitmq_broker_create_vhost` | `manage_vhost(action="create")` |
| `rabbitmq_broker_delete_vhost` | `manage_vhost(action="delete")` |
| `rabbitmq_broker_enqueue` | `publish(method="amqp_queue")` |
| `rabbitmq_broker_fanout` | `publish(method="amqp_fanout")` |
| `rabbitmq_broker_publish_message` | `publish(method="http")` |
| `rabbitmq_broker_export_definitions` | `definitions_export` |
| `rabbitmq_broker_import_definitions` | `definitions_import(partial=False)` |
| `rabbitmq_broker_update_definition` | `definitions_import(partial=True)` |
| `rabbitmq_broker_compare_definitions` | `definitions_compare` |
| `rabbitmq_broker_migrate_definitions` | `definitions_migrate` |
| `rabbitmq_broker_check_migration_readiness` | `migration_readiness` |
| `rabbitmq_broker_setup_federation` | `federation_setup` |
| `rabbitmq_broker_find_queues_by_threshold` | `find_queues` |
| `rabbitmq_broker_is_in_alarm` | `health(check="alarms")` |
| `rabbitmq_broker_is_quorum_critical` | `health(check="quorum")` |
| `rabbitmq_broker_check_local_alarms` | `health(check="alarms")` |
| `rabbitmq_broker_check_certificate_expiration` | `health(check="certificates")` |
| `rabbitmq_broker_check_protocol_listener` | `health(check="protocol")` |
| `rabbitmq_broker_check_virtual_hosts` | `health(check="vhosts")` |
| `rabbitmq_broker_list_feature_flags` | `health(check="features")` |
| `rabbitmq_broker_list_deprecated_features` | `health(check="deprecated")` |

### Tool Consolidation Summary

| v4 Tool | Actions | Replaces |
|---|---|---|
| `connect` | - | `rabbitmq_broker_initialize_connection` |
| `connect_oauth` | - | `rabbitmq_broker_initialize_connection_with_oauth` |
| `broker` | select, list | `rabbitmq_broker_select`, `rabbitmq_broker_list_registered_brokers` |
| `get_skill` | - | `rabbitmq_broker_get_skill` |
| `get_guideline` | - | `rabbitmq_broker_get_guideline` |
| `queues` | list, info, messages, bindings | `rabbitmq_broker_list_queues`, `rabbitmq_broker_get_queue_info`, `rabbitmq_broker_get_messages`, `rabbitmq_broker_get_bindings` (queue) |
| `exchanges` | list, info, bindings | `rabbitmq_broker_list_exchanges`, `rabbitmq_broker_get_exchange_info`, `rabbitmq_broker_get_bindings` (exchange) |
| `connections` | list, channels, churn, close | `rabbitmq_broker_list_connections`, `rabbitmq_broker_list_channels`, `rabbitmq_broker_get_connection_churn`, `rabbitmq_broker_close_connection` |
| `cluster` | nodes, node_info, node_memory, rebalance | `rabbitmq_broker_get_cluster_nodes_info`, `rabbitmq_broker_get_node_information`, (new: node_memory), `rabbitmq_broker_rebalance_queues` |
| `entities` | vhosts, users, consumers | `rabbitmq_broker_list_vhosts`, `rabbitmq_broker_list_users`, `rabbitmq_broker_list_consumers` |
| `policies` | list, get | `rabbitmq_broker_list_policies`, `rabbitmq_broker_get_policy` |
| `shovels` | list, get | `rabbitmq_broker_list_shovels`, `rabbitmq_broker_get_shovel_info` |
| `overview` | summary, definitions | `rabbitmq_broker_get_overview`, `rabbitmq_broker_get_broker_definition` |
| `auth` | whoami, permissions, set_permissions | `rabbitmq_broker_whoami`, `rabbitmq_broker_get_permissions`, `rabbitmq_broker_set_permissions` |
| `manage_queue` | create, delete, purge | `rabbitmq_broker_create_queue`, `rabbitmq_broker_delete_queue`, `rabbitmq_broker_purge_queue` |
| `manage_exchange` | create, delete | `rabbitmq_broker_create_exchange`, `rabbitmq_broker_delete_exchange` |
| `manage_binding` | create, delete | `rabbitmq_broker_create_binding`, `rabbitmq_broker_delete_binding` |
| `manage_policy` | create, delete | `rabbitmq_broker_create_policy`, `rabbitmq_broker_delete_policy` |
| `manage_vhost` | create, delete | `rabbitmq_broker_create_vhost`, `rabbitmq_broker_delete_vhost` |
| `publish` | amqp_queue, amqp_fanout, http | `rabbitmq_broker_enqueue`, `rabbitmq_broker_fanout`, `rabbitmq_broker_publish_message` |
| `definitions_export` | - | `rabbitmq_broker_export_definitions` |
| `definitions_import` | partial=False/True | `rabbitmq_broker_import_definitions`, `rabbitmq_broker_update_definition` |
| `definitions_compare` | - | `rabbitmq_broker_compare_definitions` |
| `definitions_migrate` | - | `rabbitmq_broker_migrate_definitions` |
| `migration_readiness` | - | `rabbitmq_broker_check_migration_readiness` |
| `federation_setup` | - | `rabbitmq_broker_setup_federation` |
| `find_queues` | - | `rabbitmq_broker_find_queues_by_threshold` |
| `health` | alarms, quorum, certificates, protocol, vhosts, features, deprecated | `rabbitmq_broker_is_in_alarm`, `rabbitmq_broker_is_quorum_critical`, `rabbitmq_broker_check_local_alarms`, `rabbitmq_broker_check_certificate_expiration`, `rabbitmq_broker_check_protocol_listener`, `rabbitmq_broker_check_virtual_hosts`, `rabbitmq_broker_list_feature_flags`, `rabbitmq_broker_list_deprecated_features` |

### Token Efficiency

Tool descriptions (docstrings) serve as idle context that LLMs must process on every request, even when a tool is not invoked. Consolidating tools with enum-based dispatch significantly reduces this overhead.

| Metric | v3 | v4 |
|---|---|---|
| Tool count | 61 | 28 |
| Total description characters | 7,213 | 3,084 |
| Reduction | - | **57.2%** |

The v4 layout saves 4,129 characters of idle tool-description context per request. Combined with fewer tool-name tokens in the tools list itself, this translates to meaningful savings in prompt token usage and faster LLM response times for multi-turn conversations.
