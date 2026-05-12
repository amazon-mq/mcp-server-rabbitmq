# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SKILLS: dict[str, dict] = {
    "pre_flight_migration_check": {
        "name": "pre_flight_migration_check",
        "description": "Check both brokers for alarms and compare definitions to report go/no-go for migration.",
        "steps": [
            "Call is_in_alarm on the source broker and record whether it returns True or False.",
            "Call is_in_alarm on the target broker and record whether it returns True or False.",
            "Call compare_definitions with source_alias and target_alias to get topology differences.",
            "If either broker is in alarm, report NO-GO with the alarm details.",
            "If compare_definitions shows differences, list them as warnings but not blockers.",
            "If no alarms and topology is identical, report GO for migration.",
        ],
        "composes": ["is_in_alarm", "compare_definitions"],
    },
    "migrate_definitions": {
        "name": "migrate_definitions",
        "description": "Export definitions from source with transforms and import to target broker.",
        "steps": [
            "Call export_definitions on the source broker with transforms like strip_cmq_keys and convert_classic_to_quorum.",
            "Review the exported definitions for any sensitive data (credentials, internal hostnames).",
            "Call import_definitions on the target broker with the exported definitions.",
            "Verify success by calling compare_definitions between source and target.",
        ],
        "composes": ["export_definitions", "import_definitions"],
    },
    "setup_federation": {
        "name": "setup_federation",
        "description": "Check federation plugin is enabled, create upstream, and create policy for message draining.",
        "steps": [
            "Call get_broker_overview on the target broker and check exchange_types for x-federation-upstream.",
            "If federation plugin is not enabled, report error and stop.",
            "Call import_definitions to create a federation upstream parameter with the source broker URI.",
            "Call import_definitions to create a policy matching the desired queue pattern with federation-upstream set.",
            "Confirm federation is active by checking the overview again for federation link status.",
        ],
        "composes": ["get_broker_overview", "import_definitions"],
    },
    "queue_metrics_analysis": {
        "name": "queue_metrics_analysis",
        "description": "Get queue info and interpret message_stats rates to report throughput and backlog.",
        "steps": [
            "Call get_queue_info for the target queue and extract messages, messages_ready, messages_unacknowledged, and message_stats.",
            "From message_stats, extract publish_details.rate (incoming msg/s) and deliver_get_details.rate (outgoing msg/s).",
            "Calculate backlog growth rate as publish_rate minus deliver_get_rate.",
            "If messages_ready is growing and deliver_get_rate is zero, flag as stalled consumers.",
            "Report: current depth, publish rate, consume rate, and whether the queue is draining or accumulating.",
        ],
        "composes": ["get_queue_info"],
    },
    "node_resource_analysis": {
        "name": "node_resource_analysis",
        "description": "Get node info, calculate memory %, disk headroom, and FD usage, then flag issues.",
        "steps": [
            "Call get_cluster_nodes_info to get all nodes with mem_used, mem_limit, disk_free, and fd_used/fd_total.",
            "Call get_node_information for each node to get detailed runtime stats including proc_used and proc_total.",
            "For each node calculate memory usage percent as (mem_used / mem_limit) * 100.",
            "For each node calculate disk headroom as disk_free minus disk_free_limit and flag if below 20% of limit.",
            "For each node calculate FD usage percent and flag if above 80%.",
            "Report a summary table with node name, memory %, disk headroom, FD %, and any alarm flags.",
        ],
        "composes": ["get_node_information", "get_cluster_nodes_info"],
    },
    "export_topology_graph": {
        "name": "export_topology_graph",
        "description": "Get all bindings, exchanges, and queues, then format as a Mermaid diagram.",
        "steps": [
            "Call list_exchanges to get all exchange names and types.",
            "Call list_queues to get all queue names.",
            "Call get_bindings (no filter) to get all bindings in the vhost.",
            "Start a Mermaid graph TD block.",
            "For each exchange, add a node with shape and label including exchange type.",
            "For each queue, add a node with rounded shape.",
            "For each binding, add an edge from source exchange to destination with routing_key as label.",
            "Return the complete Mermaid diagram as a code block.",
        ],
        "composes": ["list_exchanges", "list_queues", "get_bindings"],
    },
    "trace_message_route": {
        "name": "trace_message_route",
        "description": "Trace where a message with a given routing key would go through an exchange.",
        "steps": [
            "Call get_exchange_info for the target exchange to determine its type (direct, topic, fanout, headers).",
            "Call get_bindings filtered by that exchange to get all outbound bindings with routing_keys.",
            "If exchange type is fanout, all bound destinations receive the message.",
            "If exchange type is direct, filter bindings where routing_key exactly matches the provided key.",
            "If exchange type is topic, apply AMQP topic matching (# = multi-word, * = single-word) against bindings.",
            "List all destination queues/exchanges that would receive the message.",
        ],
        "composes": ["get_exchange_info", "get_bindings"],
    },
    "find_orphaned_queues": {
        "name": "find_orphaned_queues",
        "description": "Find queues with no bindings and no consumers (orphaned).",
        "steps": [
            "Call list_queues to get all queue names.",
            "Call get_bindings (no filter) to get all bindings in the vhost.",
            "Call list_consumers to get all active consumers.",
            "Build a set of queue names that appear as binding destinations.",
            "Build a set of queue names that have at least one consumer.",
            "Any queue not in either set is orphaned — list them with their message count from get_queue_info.",
        ],
        "composes": ["list_queues", "get_bindings", "list_consumers"],
    },
    "find_unbound_exchanges": {
        "name": "find_unbound_exchanges",
        "description": "Find exchanges with no outbound bindings, excluding default amq.* exchanges.",
        "steps": [
            "Call list_exchanges to get all exchange names.",
            "Call get_bindings (no filter) to get all bindings.",
            "Build a set of exchange names that appear as source in at least one binding.",
            "Filter out exchanges whose name starts with amq. or is empty string (default exchange).",
            "Any remaining exchange not in the source set is unbound — report them.",
        ],
        "composes": ["list_exchanges", "get_bindings"],
    },
    "trace_dead_letter_chain": {
        "name": "trace_dead_letter_chain",
        "description": "Trace the dead-letter chain from a queue by following x-dead-letter-exchange arguments.",
        "steps": [
            "Call get_queue_info for the starting queue and extract arguments.x-dead-letter-exchange and arguments.x-dead-letter-routing-key.",
            "If no DLX is configured, report that this queue has no dead-letter routing and stop.",
            "Call get_bindings filtered by the DLX exchange to find which queue receives dead-lettered messages.",
            "Call get_queue_info on the destination DLQ and check if it also has a DLX configured.",
            "Repeat recursively until you find a queue with no DLX or detect a cycle.",
            "Report the full chain as: source_queue -> DLX exchange -> DLQ -> (next hop or terminal).",
        ],
        "composes": ["get_queue_info", "get_bindings"],
    },
    "inspect_dead_letters": {
        "name": "inspect_dead_letters",
        "description": "Peek at DLQ messages and extract x-death headers showing source queue, reason, and timestamp.",
        "steps": [
            "Call get_messages on the DLQ with count=5 and ackmode=ack_requeue_true to peek without consuming.",
            "For each message, extract the properties.headers.x-death array.",
            "From each x-death entry, extract queue (original source), reason (rejected/expired/maxlen), time, and count.",
            "Group messages by source queue and reason.",
            "Report a summary: how many messages from each source, the primary rejection reason, and the time range.",
        ],
        "composes": ["get_messages"],
    },
    "dlq_summary": {
        "name": "dlq_summary",
        "description": "Find DLQs via naming pattern or DLX config, peek messages, and group by source and reason.",
        "steps": [
            "Call list_queues and filter for queues matching common DLQ patterns (containing dlq, dead-letter, or .dl).",
            "For any remaining queues, call get_queue_info and check if they are targets of a DLX binding.",
            "For each identified DLQ, call get_messages with count=10 to sample the dead-letter contents.",
            "Extract x-death headers from each message to determine source queue and rejection reason.",
            "Group findings by DLQ name, then by source queue, then by reason.",
            "Report: DLQ name, message count, top sources, and most common rejection reasons.",
        ],
        "composes": ["list_queues", "get_queue_info", "get_messages"],
    },
    "broker_recommendations": {
        "name": "broker_recommendations",
        "description": "Analyze broker config against best practices and produce prioritized recommendations.",
        "steps": [
            "Call get_broker_overview to get cluster size, RabbitMQ version, and Erlang version.",
            "Call get_cluster_nodes_info to assess resource utilization across all nodes.",
            "Call list_queues and for any queue count above 1000, flag as potential concern.",
            "Call get_guideline with rabbitmq_broker_setup_best_practices_guide to load best practices.",
            "Compare: queue types (classic vs quorum), HA policies, memory watermarks, disk thresholds against guidelines.",
            "Produce a prioritized list of findings: Critical (alarms, near-limit resources), Warning (suboptimal config), Info (nice-to-have improvements).",
        ],
        "composes": [
            "get_broker_overview",
            "get_cluster_nodes_info",
            "list_queues",
            "get_guideline",
        ],
    },
    "queue_health_assessment": {
        "name": "queue_health_assessment",
        "description": "Assess a queue's health by checking type, consumers, depth, and policy coverage.",
        "steps": [
            "Call get_queue_info for the target queue and extract type, consumers, messages, policy, and arguments.",
            "Call get_guideline with rabbitmq_quorum_queue_migration_guide if the queue is classic type.",
            "Check if queue has zero consumers and non-zero messages — flag as potentially abandoned or stalled.",
            "Check if queue type is classic mirrored — recommend migration to quorum.",
            "Check if queue has a max-length or TTL policy applied — note overflow behavior.",
            "Report: queue health status (healthy/warning/critical), findings, and specific recommended actions.",
        ],
        "composes": ["get_queue_info", "get_guideline"],
    },
    "resource_headroom_check": {
        "name": "resource_headroom_check",
        "description": "Compute memory/disk/FD usage percentages vs watermarks and project time-to-alarm.",
        "steps": [
            "Call get_cluster_nodes_info to get mem_used, mem_limit, disk_free, disk_free_alarm threshold for each node.",
            "Calculate memory headroom: (mem_limit - mem_used) / mem_limit * 100 for each node.",
            "Calculate disk headroom: how much free disk remains above the alarm watermark.",
            "Calculate FD headroom: (fd_total - fd_used) / fd_total * 100.",
            "If any resource is above 80% utilization, flag as WARNING; above 90% flag as CRITICAL.",
            "Report a table: node, memory headroom %, disk headroom %, FD headroom %, and overall status.",
        ],
        "composes": ["get_cluster_nodes_info"],
    },
    "policy_conflict_detection": {
        "name": "policy_conflict_detection",
        "description": "Find overlapping policy regex patterns and report which policy wins by priority.",
        "steps": [
            "Call list_policies to get all policies with their pattern, priority, and apply-to fields.",
            "For each pair of policies, test if their regex patterns could match the same queue/exchange name.",
            "When two policies overlap, the one with higher priority wins — note the conflict and winner.",
            "Flag any policies with identical patterns but different priorities as definite conflicts.",
            "Flag any policy with pattern .* as it matches everything and may shadow more specific policies.",
            "Report: list of conflicts, which policy wins each conflict, and queues/exchanges potentially affected.",
        ],
        "composes": ["list_policies"],
    },
}
