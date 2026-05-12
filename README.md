# mcp-server-rabbitmq

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for RabbitMQ broker management and operations.

## Features

- **61 tools** for broker management — connections, queues, exchanges, health checks, observability, and blue-green migration
- **16 composable skills** — topology visualization, dead letter analysis, capacity planning, and more
- **Multi-broker support** — connect multiple brokers simultaneously, switch between them by alias
- **Mutative tools gated** behind `--allow-mutative-tools` flag (off by default for safety)

## Quick Start

### Install via PyPI

```bash
pip install amq-mcp-server-rabbitmq
# or
uv pip install amq-mcp-server-rabbitmq
```

### Configure in Claude Desktop

```json
{
  "mcpServers": {
    "rabbitmq": {
      "command": "uvx",
      "args": [
        "amq-mcp-server-rabbitmq@latest",
        "--allow-mutative-tools"
      ]
    }
  }
}
```

### Basic Usage

Once configured, the agent can connect to your broker and manage it conversationally:

```
You: Connect to my RabbitMQ broker at rabbitmq.example.com with user admin
You: List all queues and show me which ones have messages backing up
You: Create a dead letter exchange and bind it to the orders queue
```

## Configuration

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--allow-mutative-tools` | Enable tools that can create, modify, or delete resources (default: off) |
| `--management-port` | RabbitMQ Management API port (default: 443 for TLS, 15672 for non-TLS) |
| `--http` | Use Streamable HTTP transport instead of stdio |
| `--server-port` | Port to run the MCP server on (default: 8888) |
| `--http-auth-jwks-uri` | JWKS URI for Bearer Auth Provider |
| `--http-auth-issuer` | Issuer for Bearer Auth Provider |
| `--http-auth-audience` | Audience for Bearer Auth Provider |
| `--http-auth-required-scopes` | Required scopes for Bearer Auth Provider |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `FASTMCP_LOG_LEVEL` | Log level: DEBUG, INFO, WARNING (default), ERROR |

## Tools

### Connection and Session (6 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_initialize_connection` | Connect to a broker with username/password (SIMPLE auth) |
| `rabbitmq_broker_initialize_connection_with_oauth` | Connect to a broker using an OAuth token |
| `rabbitmq_broker_select` | Switch the active broker by alias |
| `rabbitmq_broker_list_registered_brokers` | List all registered broker connections and which is active |
| `rabbitmq_broker_get_guideline` | Get best-practice guidelines for RabbitMQ deployment and sizing |
| `rabbitmq_broker_get_skill` | Get a composable workflow recipe (see Skills section below) |

### Read-Only: Queues and Exchanges (7 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_list_queues` | List all queues in the broker |
| `rabbitmq_broker_list_exchanges` | List all exchanges in the broker |
| `rabbitmq_broker_list_vhosts` | List all virtual hosts |
| `rabbitmq_broker_get_queue_info` | Get detailed information about a specific queue |
| `rabbitmq_broker_get_exchange_info` | Get detailed information about a specific exchange |
| `rabbitmq_broker_get_bindings` | Get bindings, optionally filtered by queue or exchange |
| `rabbitmq_broker_get_messages` | Peek at messages in a queue without consuming them |

### Read-Only: Connections and Consumers (4 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_list_connections` | List all connections on the broker |
| `rabbitmq_broker_list_consumers` | List all consumers on the broker |
| `rabbitmq_broker_list_channels` | List all open channels on the broker |
| `rabbitmq_broker_list_users` | List all users on the broker |

### Read-Only: Cluster and Nodes (2 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_get_cluster_nodes_info` | Get the list of nodes and their info in the cluster |
| `rabbitmq_broker_get_node_information` | Get detailed node info including memory, disk, uptime |

### Read-Only: Policies and Shovels (4 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_list_policies` | List all policies in a virtual host |
| `rabbitmq_broker_get_policy` | Get a specific policy by name |
| `rabbitmq_broker_list_shovels` | List all shovels on the broker |
| `rabbitmq_broker_get_shovel_info` | Get detailed information about a specific shovel |

### Read-Only: Permissions and Identity (2 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_get_permissions` | Get permissions for a user in a virtual host |
| `rabbitmq_broker_whoami` | Get the current authenticated user |

### Read-Only: Definitions and Migration (3 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_get_broker_definition` | Get full broker definitions (exchanges, queues, bindings, users, etc.) |
| `rabbitmq_broker_compare_definitions` | Compare definitions between two connected brokers |
| `rabbitmq_broker_check_migration_readiness` | Pre-flight check for blue-green migration |

### Read-Only: Observability (3 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_get_overview` | Get cluster-wide stats: version, node count, message rates, object totals |
| `rabbitmq_broker_find_queues_by_threshold` | Find queues by criteria: depth, idle time, no consumers, unacked messages |
| `rabbitmq_broker_get_connection_churn` | Get connection/channel open and close rates |

### Health Checks (8 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_is_in_alarm` | Check if the broker is in alarm |
| `rabbitmq_broker_is_quorum_critical` | Check if quorum queues have minimum online quorum |
| `rabbitmq_broker_check_local_alarms` | Check for local alarms on the active broker |
| `rabbitmq_broker_check_certificate_expiration` | Check if TLS certificates expire within a timeframe |
| `rabbitmq_broker_check_protocol_listener` | Check if a protocol listener is active |
| `rabbitmq_broker_check_virtual_hosts` | Check health of all virtual hosts |
| `rabbitmq_broker_list_feature_flags` | List all feature flags and their status |
| `rabbitmq_broker_list_deprecated_features` | List deprecated features currently in use |

### Mutative: CRUD (16 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_create_queue` | Create a queue (quorum, classic, or stream) |
| `rabbitmq_broker_delete_queue` | Delete a specific queue |
| `rabbitmq_broker_purge_queue` | Remove all messages from a queue |
| `rabbitmq_broker_create_exchange` | Create an exchange (direct, fanout, topic, headers) |
| `rabbitmq_broker_delete_exchange` | Delete a specific exchange |
| `rabbitmq_broker_create_binding` | Create a binding from an exchange to a queue |
| `rabbitmq_broker_delete_binding` | Delete a binding |
| `rabbitmq_broker_create_policy` | Create or update a policy |
| `rabbitmq_broker_delete_policy` | Delete a policy |
| `rabbitmq_broker_create_vhost` | Create a virtual host |
| `rabbitmq_broker_delete_vhost` | Delete a virtual host and all its resources |
| `rabbitmq_broker_set_permissions` | Set permissions for a user in a virtual host |
| `rabbitmq_broker_close_connection` | Close a specific connection by name |
| `rabbitmq_broker_update_definition` | Update server definitions |
| `rabbitmq_broker_export_definitions` | Export definitions with optional transformations |
| `rabbitmq_broker_import_definitions` | Import definitions to the active broker |

### Mutative: Migration (4 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_migrate_definitions` | Export, transform, and import definitions between brokers |
| `rabbitmq_broker_setup_federation` | Set up federation upstream and policy for message draining |
| `rabbitmq_broker_rebalance_queues` | Rebalance queue leaders across cluster nodes |
| `rabbitmq_broker_publish_message` | Publish a message via HTTP Management API (diagnostics) |

### Mutative: AMQP (2 tools)

| Tool | Description |
|------|-------------|
| `rabbitmq_broker_enqueue` | Publish a message to a specific queue via AMQP |
| `rabbitmq_broker_fanout` | Publish a message to a fanout exchange via AMQP |

## Skills

Skills are composable workflows accessed via `rabbitmq_broker_get_skill`. They guide the agent through multi-step operations by orchestrating existing tools — no additional code required.

| Skill | What it does | Tools it composes |
|-------|-------------|-------------------|
| `pre_flight_migration_check` | Check alarms on both brokers + compare definitions for go/no-go | is_in_alarm, compare_definitions |
| `migrate_definitions` | Export from source with transforms, import to target | export_definitions, import_definitions |
| `setup_federation` | Verify federation plugin, create upstream and policy | get_broker_overview, import_definitions |
| `queue_metrics_analysis` | Interpret publish/deliver rates and backlog trends | get_queue_info |
| `node_resource_analysis` | Calculate memory %, disk headroom, FD usage per node | get_node_information, get_cluster_nodes_info |
| `export_topology_graph` | Generate Mermaid diagram of exchange-binding-queue graph | list_exchanges, list_queues, get_bindings |
| `trace_message_route` | Predict which queues receive a message given exchange + routing key | get_exchange_info, get_bindings |
| `find_orphaned_queues` | Find queues with no bindings and no consumers | list_queues, get_bindings, list_consumers |
| `find_unbound_exchanges` | Find exchanges with no outbound bindings (excluding amq.*) | list_exchanges, get_bindings |
| `trace_dead_letter_chain` | Walk x-dead-letter-exchange arguments to map the full DLX chain | get_queue_info, get_bindings |
| `inspect_dead_letters` | Peek at DLQ messages and extract x-death headers (source, reason) | get_messages |
| `dlq_summary` | Aggregate dead letters by source queue and rejection reason | list_queues, get_queue_info, get_messages |
| `broker_recommendations` | Compare live broker state against best-practice guidelines | get_broker_overview, get_cluster_nodes_info, list_queues, get_guideline |
| `queue_health_assessment` | Assess queue type, consumers, depth, and policy coverage | get_queue_info, get_guideline |
| `resource_headroom_check` | Compute resource utilization % vs watermarks, project time-to-alarm | get_cluster_nodes_info |
| `policy_conflict_detection` | Find overlapping policy patterns and report priority winners | list_policies |

## Development

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Running Locally

```bash
git clone https://github.com/amazon-mq/mcp-server-rabbitmq.git
cd mcp-server-rabbitmq
uv run amq-mcp-server-rabbitmq
```

### Testing

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check . && uv run ruff format .
```

### Docker (Local RabbitMQ)

```bash
docker-compose up
```

This starts RabbitMQ 4 with the management plugin on `localhost:5672` (AMQP) and `localhost:15672` (Management UI). Default credentials: `guest` / `guest`.

## Security

- **Mutative tools disabled by default** — pass `--allow-mutative-tools` to opt in
- **TLS by default** — connections use `use_tls=True` and port 5671 unless overridden
- **OAuth support** — connect with access tokens instead of username/password
- **HTTP transport with JWKS auth** — run as a remote server with Bearer token validation via configurable IdP

## License

Apache-2.0 — see [LICENSE](LICENSE) for details.
