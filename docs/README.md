# Documentation

Guides for the RabbitMQ MCP server. Start with the [project README](../README.md) for install and the full tool/skill reference, then dive into the topic guides here.

> **Tool names:** these guides use the **v3 tool names** (e.g. `rabbitmq_broker_list_queues`). In
> **v4 mode** (`--v4`) the same operations are reached through consolidated dispatchers
> (e.g. `queues(action="list")`). See the [v4 Mode section](../README.md#v4-mode) and the
> [migration guide in the CHANGELOG](../CHANGELOG.md) for the full v3 → v4 name mapping. Concepts
> and workflows are identical between modes.

| Guide | What it covers |
|-------|----------------|
| [Multi-Broker](./multi-broker.md) | Registering and switching between multiple brokers by alias |
| [Authentication](./authentication.md) | Broker auth (SIMPLE / OAuth) and HTTP-transport JWT/JWKS Bearer auth |
| [Skills](./skills.md) | The 16 composable workflow recipes and how the agent uses them |
| [Migration](./migration.md) | Blue-green migration: readiness checks, definition transforms, federation draining |
| [CHANGELOG](../CHANGELOG.md) | Version history |

## What this server is

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes RabbitMQ broker
management as MCP tools. It talks to the broker two ways:

- **Management HTTP API** (`src/rabbitmq/admin.py`) for read/observability/CRUD/health operations
- **AMQP via pika** (`src/rabbitmq/connection.py`) for `enqueue` / `fanout` message publishing

61 tools and 16 skills, with mutative tools gated off by default. See the [top-level README](../README.md#tools)
for the complete table.
