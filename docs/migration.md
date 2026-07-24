# Blue-Green Migration

The server supports migrating a RabbitMQ workload from one broker (blue/source) to another
(green/target) by connecting to both at once and moving topology + messages across. This is the
primary use case behind [multi-broker support](./multi-broker.md).

## Overview

```
  source (blue)                          target (green)
  ┌──────────────┐   1. compare/readiness  ┌──────────────┐
  │ exchanges    │ ──────────────────────► │              │
  │ queues       │   2. migrate defs        │  (recreated) │
  │ bindings     │      + transforms        │              │
  │ policies     │ ──────────────────────► │              │
  └──────┬───────┘   3. federation drain    └──────▲───────┘
         └───────────── messages flow ─────────────┘
```

## Step 1 — Readiness

Before moving anything, verify both brokers are healthy and understand the topology delta.

| Tool | Purpose |
|------|---------|
| `rabbitmq_broker_check_migration_readiness` | Pre-flight checks on the active broker |
| `rabbitmq_broker_compare_definitions` | Diff exchanges/queues/bindings/policies between two aliases |
| `rabbitmq_broker_is_in_alarm` | Confirm neither broker is in a memory/disk alarm |

Or run the `pre_flight_migration_check` [skill](./skills.md), which composes alarm checks on both
brokers with a definition comparison and returns a go/no-go.

## Step 2 — Move definitions

`rabbitmq_broker_migrate_definitions` (or the `migrate_definitions` skill) exports from the source,
applies transforms, and imports into the target. Transforms are named and applied in order
(`src/rabbitmq/transforms.py`, matching `rabbitmqadmin-ng` capabilities):

| Transform | Effect |
|-----------|--------|
| `strip_cmq_keys` | Remove classic mirrored-queue policy keys (`ha-mode`, `ha-params`, …) obsolete on modern RabbitMQ |
| `convert_classic_to_quorum` | Rewrite classic queues as quorum queues during the copy |
| `drop_empty_policies` | Drop policies left with no definition keys after other transforms |
| `obfuscate_credentials` | Redact credentials in the exported definitions |
| `exclude_users` | Omit user records from the export |
| `exclude_permissions` | Omit permission records from the export |

Passing an unknown transform name raises an error listing the valid options.

Related lower-level tools: `rabbitmq_broker_export_definitions`, `rabbitmq_broker_import_definitions`,
`rabbitmq_broker_update_definition`.

> Review exported definitions for sensitive data (credentials, internal hostnames) before importing.

## Step 3 — Drain messages

Once topology exists on the target, move in-flight messages:

- **Federation** — `rabbitmq_broker_setup_federation` registers the source as an upstream and applies
  a policy so the target pulls messages across. Use the `setup_federation` skill to verify the plugin
  is enabled first.
- **Shovels** — inspect existing shovels with `rabbitmq_broker_list_shovels` /
  `rabbitmq_broker_get_shovel_info`.

## Step 4 — Rebalance & verify

- `rabbitmq_broker_rebalance_queues` — spread quorum/stream queue leaders across target nodes.
- `rabbitmq_broker_compare_definitions` — confirm the target matches the source.
- `rabbitmq_broker_find_queues_by_threshold` — confirm backlogs have drained (depth, unacked).

## Safety notes

- All mutative migration tools require the server to be started with `--allow-mutative-tools`.
- Migration reads/writes go through the Management HTTP API with per-request timeouts, so a stalled
  broker surfaces as an error rather than a hang.
- Nothing is deleted on the source by these tools; cutover and source teardown remain a deliberate,
  separate step you perform once verification passes.
