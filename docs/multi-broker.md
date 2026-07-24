# Multi-Broker Support

The server can hold connections to several brokers at once and route every tool call to whichever
broker is currently *active*. This is what makes blue-green migration and cross-broker comparison
possible in a single session.

## Model

- Each connection is registered under an **alias** you choose (e.g. `source`, `target`, `prod-uw2`).
- Exactly one broker is **active** at a time. Read/mutative tools operate on the active broker.
- Switching is instant and does not drop the other connections.

## Registering brokers

Connect with username/password (SIMPLE auth):

```
You: Connect to rabbitmq-blue.example.com as user admin, call it "source"
  -> rabbitmq_broker_initialize_connection(alias="source", ...)

You: Connect to rabbitmq-green.example.com with the same creds, call it "target"
  -> rabbitmq_broker_initialize_connection(alias="target", ...)
```

Connect with an OAuth access token instead of a password:

```
  -> rabbitmq_broker_initialize_connection_with_oauth(alias="prod", token="...")
```

See [Authentication](./authentication.md) for how broker auth and server auth differ.

## Switching and listing

| Tool | Purpose |
|------|---------|
| `rabbitmq_broker_select` | Make a registered alias the active broker |
| `rabbitmq_broker_list_registered_brokers` | Show all registered aliases and which is active |

```
You: Which brokers am I connected to?
  -> rabbitmq_broker_list_registered_brokers
     source (active), target

You: Switch to target
  -> rabbitmq_broker_select(alias="target")
```

## Why it matters for migration

Cross-broker tools read the alias-keyed registry directly, so you can compare or copy between two
live brokers without reconnecting:

- `rabbitmq_broker_compare_definitions` — diff topology between two aliases
- `rabbitmq_broker_migrate_definitions` — export from source, transform, import into target

See the [Migration guide](./migration.md).

## Defaults and safety

- Connections default to **TLS on port 5671** (`use_tls=True`); pass explicit host/port to override.
- The Management API port defaults to 443 (TLS) or 15672 (non-TLS); override with `--management-port`.
- Credentials are never stored pre-encoded; auth headers are generated per request.
