# Skills

Skills are **composable workflow recipes** — not extra code and not extra API calls to RabbitMQ.
Each skill is a structured set of steps that tells the agent how to orchestrate the existing tools to
accomplish a multi-step task. The agent fetches a skill, then executes the underlying tools itself.

## How they work

Skills live in `src/rabbitmq/skills.py` as a dictionary. Each entry has:

| Field | Meaning |
|-------|---------|
| `name` | Skill identifier |
| `description` | One line on what it accomplishes |
| `steps` | Ordered natural-language instructions the agent follows |
| `composes` | The underlying tools the steps call |

The agent retrieves a recipe with:

```
rabbitmq_broker_get_skill(skill_name="dlq_summary")
```

and then runs the tools named in `composes`, following `steps`. Because a skill is just guidance over
tools that already exist, adding a skill never widens the server's actual capabilities or its
mutative surface.

## The 16 skills

### Migration & federation
- `pre_flight_migration_check` — alarms on both brokers + definition diff → go/no-go
- `migrate_definitions` — export from source with transforms, import into target
- `setup_federation` — verify plugin, create upstream + policy for draining

### Observability & capacity
- `queue_metrics_analysis` — interpret publish/deliver rates and backlog trend
- `node_resource_analysis` — memory %, disk headroom, FD usage per node
- `resource_headroom_check` — utilization vs watermarks, project time-to-alarm
- `broker_recommendations` — compare live state against best-practice guidelines
- `queue_health_assessment` — queue type, consumers, depth, policy coverage

### Topology
- `export_topology_graph` — Mermaid diagram of exchange → binding → queue
- `trace_message_route` — predict which queues receive a message for a routing key
- `find_orphaned_queues` — queues with no bindings and no consumers
- `find_unbound_exchanges` — exchanges with no outbound bindings (excluding `amq.*`)
- `policy_conflict_detection` — overlapping policy patterns and priority winners

### Dead-letter analysis
- `trace_dead_letter_chain` — walk `x-dead-letter-exchange` args to map the DLX chain
- `inspect_dead_letters` — peek DLQ messages, extract `x-death` (source, reason)
- `dlq_summary` — aggregate dead letters by source queue and rejection reason

## Example

```
You: Summarize the dead letters across my broker

Agent: (fetches dlq_summary skill, then:)
  1. list_queues -> finds queues ending in .dlq / with dead-letter args
  2. get_queue_info on each -> depth
  3. get_messages (peek) -> reads x-death headers
  -> "3 DLQs, 412 messages total. orders.dlq: 380 (rejected: max-retries),
      payments.dlq: 30 (expired), audit.dlq: 2 (rejected)."
```

## Adding a skill

Add an entry to the `SKILLS` dict in `src/rabbitmq/skills.py` with `name`, `description`, `steps`,
and `composes`. Keep `steps` concrete and reference only tools listed in `composes`. No registration
elsewhere is required — `rabbitmq_broker_get_skill` reads the dict directly.
