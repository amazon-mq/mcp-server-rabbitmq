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

"""v4 consolidated tool module: 59 tools merged into 28 enum-based dispatchers."""

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .admin import RabbitMQAdmin
from .connection import RabbitMQConnection, validate_hostname, validate_rabbitmq_name
from .handlers import (
    handle_check_certificate_expiration,
    handle_check_local_alarms,
    handle_check_migration_readiness,
    handle_check_protocol_listener,
    handle_check_virtual_hosts,
    handle_close_connection,
    handle_compare_definitions,
    handle_create_binding,
    handle_create_exchange,
    handle_create_policy,
    handle_create_queue,
    handle_create_vhost,
    handle_delete_binding,
    handle_delete_exchange,
    handle_delete_policy,
    handle_delete_queue,
    handle_delete_vhost,
    handle_enqueue,
    handle_export_definitions,
    handle_fanout,
    handle_find_queues_by_threshold,
    handle_get_bindings,
    handle_get_broker_overview,
    handle_get_cluster_nodes,
    handle_get_cluster_node_memory,
    handle_get_connection_churn,
    handle_get_definition,
    handle_get_exchange_info,
    handle_get_guidelines,
    handle_get_messages,
    handle_get_node_information,
    handle_get_permissions,
    handle_get_policy,
    handle_get_queue_info,
    handle_get_skill,
    handle_import_definitions,
    handle_is_broker_in_alarm,
    handle_is_node_in_quorum_critical,
    handle_list_channels,
    handle_list_connections,
    handle_list_consumers,
    handle_list_deprecated_features,
    handle_list_exchanges,
    handle_list_exchanges_by_vhost,
    handle_list_feature_flags,
    handle_list_policies,
    handle_list_queues,
    handle_list_queues_by_vhost,
    handle_list_shovels,
    handle_list_users,
    handle_list_vhosts,
    handle_publish_message,
    handle_purge_queue,
    handle_rebalance_queues,
    handle_set_permissions,
    handle_setup_federation,
    handle_shovel,
    handle_update_definition,
    handle_whoami,
)


TOOL_GROUPS = ("core", "read", "mutative", "migration", "observability", "health")


class RabbitMQModuleV4:
    """v4 consolidated module: fewer tools, enum-based dispatch, dynamic loading."""

    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.brokers: dict[str, dict] = {}
        self.active_alias: str | None = None
        self.default_management_port: int | None = None
        self._mutative_enabled: bool = False

    def _get_admin(self) -> RabbitMQAdmin:
        if not self.active_alias or self.active_alias not in self.brokers:
            raise AssertionError("No active broker. Call connect first.")
        return self.brokers[self.active_alias]["rmq_admin"]

    def _get_rmq(self) -> RabbitMQConnection:
        if not self.active_alias or self.active_alias not in self.brokers:
            raise AssertionError("No active broker. Call connect first.")
        return self.brokers[self.active_alias]["rmq"]

    def register_tools(
        self,
        groups: tuple[str, ...] = TOOL_GROUPS,
    ):
        """Register tool groups dynamically."""
        if "mutative" in groups:
            self._mutative_enabled = True
        if "core" in groups:
            self._register_core()
        if "read" in groups:
            self._register_read()
        if "mutative" in groups:
            self._register_mutative()
        if "migration" in groups:
            self._register_migration()
        if "observability" in groups:
            self._register_observability()
        if "health" in groups:
            self._register_health()

    def _register_core(self):
        @self.mcp.tool()
        def connect(
            hostname: str,
            username: str,
            password: str,
            port: int = 5671,
            use_tls: bool = True,
            alias: str | None = None,
        ) -> str:
            """Connect to a RabbitMQ broker. Use alias to manage multiple brokers (e.g. 'blue', 'green')."""
            validate_hostname(hostname)
            alias = alias or hostname
            rmq = RabbitMQConnection(hostname=hostname, username=username, password=password, port=port, use_tls=use_tls)
            rmq_admin = RabbitMQAdmin(hostname=hostname, username=username, password=password, use_tls=use_tls, port=self.default_management_port)
            try:
                rmq_admin.test_connection()
            except Exception as e:
                raise ValueError(f"Failed to connect to {hostname}: {e}")
            self.brokers[alias] = {"rmq": rmq, "rmq_admin": rmq_admin, "hostname": hostname}
            self.active_alias = alias
            return f"Connected to {hostname} as '{alias}'"

        @self.mcp.tool()
        def connect_oauth(hostname: str, oauth_token: str, alias: str | None = None) -> str:
            """Connect using OAuth token."""
            validate_hostname(hostname)
            alias = alias or hostname
            rmq = RabbitMQConnection(hostname=hostname, username="", password=oauth_token)
            rmq_admin = RabbitMQAdmin(hostname=hostname, username="", password=oauth_token, port=self.default_management_port)
            try:
                rmq_admin.test_connection()
            except Exception as e:
                raise ValueError(f"Failed to connect to {hostname}: {e}")
            self.brokers[alias] = {"rmq": rmq, "rmq_admin": rmq_admin, "hostname": hostname}
            self.active_alias = alias
            return f"Connected to {hostname} as '{alias}'"

        @self.mcp.tool()
        def broker(action: Literal["select", "list"], alias: str | None = None) -> Any:
            """Manage broker connections. select: switch active broker. list: show all."""
            if action == "list":
                return [{"alias": a, "hostname": i["hostname"], "active": a == self.active_alias} for a, i in self.brokers.items()]
            if action == "select":
                if not alias or alias not in self.brokers:
                    raise ValueError(f"Unknown alias. Available: {', '.join(self.brokers.keys())}")
                self.active_alias = alias
                return f"Active: '{alias}' ({self.brokers[alias]['hostname']})"

        @self.mcp.tool()
        def get_skill(skill_name: str) -> str:
            """Workflow recipe. Available: pre_flight_migration_check, migrate_definitions, setup_federation, queue_metrics_analysis, node_resource_analysis, export_topology_graph, trace_message_route, find_orphaned_queues, find_unbound_exchanges, trace_dead_letter_chain, inspect_dead_letters, dlq_summary, broker_recommendations, queue_health_assessment, resource_headroom_check, policy_conflict_detection"""
            return handle_get_skill(skill_name)

        @self.mcp.tool()
        def get_guideline(name: str) -> str:
            """Best practice guide. Available: rabbitmq_broker_sizing_guide, rabbitmq_broker_setup_best_practices_guide, rabbitmq_quorum_queue_migration_guide, rabbitmq_client_performance_optimization_guide, rabbitmq_production_deployment_guidelines"""
            return str(handle_get_guidelines(name))

    def _register_read(self):
        @self.mcp.tool()
        def queues(
            action: Literal["list", "info", "messages", "bindings"] = "list",
            name: str | None = None,
            vhost: str = "/",
            count: int = 1,
        ) -> Any:
            """Queue operations. list: all queues. info: details for one. messages: peek. bindings: show bindings."""
            admin = self._get_admin()
            if action == "list":
                return handle_list_queues_by_vhost(admin, vhost)
            if action == "info":
                if not name:
                    raise ValueError("name required for info")
                return handle_get_queue_info(admin, name, vhost)
            if action == "messages":
                if not name:
                    raise ValueError("name required for messages")
                return handle_get_messages(admin, name, vhost, count)
            if action == "bindings":
                return handle_get_bindings(admin, queue=name, vhost=vhost)

        @self.mcp.tool()
        def exchanges(
            action: Literal["list", "info", "bindings"] = "list",
            name: str | None = None,
            vhost: str = "/",
        ) -> Any:
            """Exchange operations. list: all exchanges. info: details. bindings: show bindings."""
            admin = self._get_admin()
            if action == "list":
                return handle_list_exchanges_by_vhost(admin, vhost)
            if action == "info":
                if not name:
                    raise ValueError("name required for info")
                return handle_get_exchange_info(admin, name, vhost)
            if action == "bindings":
                return handle_get_bindings(admin, exchange=name, vhost=vhost)

        @self.mcp.tool()
        def connections(
            action: Literal["list", "channels", "churn"] = "list",
            name: str | None = None,
        ) -> Any:
            """Connection operations. list: all connections. channels: all channels. churn: open/close rates."""
            admin = self._get_admin()
            if action == "list":
                return handle_list_connections(admin)
            if action == "channels":
                return handle_list_channels(admin)
            if action == "churn":
                return handle_get_connection_churn(admin)

        @self.mcp.tool()
        def cluster(
            action: Literal["nodes", "node_info", "node_memory"] = "nodes",
            node_name: str | None = None,
        ) -> Any:
            """Cluster operations. nodes: list. node_info/node_memory: details for one node."""
            admin = self._get_admin()
            if action == "nodes":
                return handle_get_cluster_nodes(admin)
            if action == "node_info":
                if not node_name:
                    raise ValueError("node_name required")
                return handle_get_node_information(admin, node_name)
            if action == "node_memory":
                if not node_name:
                    raise ValueError("node_name required")
                return handle_get_cluster_node_memory(admin, node_name)

        @self.mcp.tool()
        def entities(action: Literal["vhosts", "users", "consumers"]) -> list:
            """List entities. vhosts: all virtual hosts. users: all users. consumers: all consumers."""
            admin = self._get_admin()
            if action == "vhosts":
                return handle_list_vhosts(admin)
            if action == "users":
                return handle_list_users(admin)
            if action == "consumers":
                return handle_list_consumers(admin)

        @self.mcp.tool()
        def policies(
            action: Literal["list", "get"] = "list",
            name: str | None = None,
            vhost: str = "/",
        ) -> Any:
            """Policy operations. list: all policies. get: one by name."""
            admin = self._get_admin()
            if action == "list":
                return handle_list_policies(admin, vhost)
            if action == "get":
                if not name:
                    raise ValueError("name required for get")
                return handle_get_policy(admin, name, vhost)

        @self.mcp.tool()
        def shovels(
            action: Literal["list", "get"] = "list",
            name: str | None = None,
            vhost: str = "/",
        ) -> Any:
            """Shovel operations. list: all shovels. get: one by name."""
            admin = self._get_admin()
            if action == "list":
                return handle_list_shovels(admin)
            if action == "get":
                if not name:
                    raise ValueError("name required for get")
                return handle_shovel(admin, name, vhost)

        @self.mcp.tool()
        def overview(action: Literal["summary", "definitions"] = "summary") -> dict:
            """Broker overview. summary: version, totals, rates, listeners. definitions: full broker definitions (queues, exchanges, bindings, users, vhosts, permissions)."""
            admin = self._get_admin()
            if action == "summary":
                return handle_get_broker_overview(admin)
            if action == "definitions":
                return handle_get_definition(admin)

        @self.mcp.tool()
        def auth(
            action: Literal["whoami", "permissions"] = "whoami",
            vhost: str = "/",
            user: str = "guest",
        ) -> Any:
            """Auth operations. whoami: current user. permissions: get permissions for user in vhost."""
            admin = self._get_admin()
            if action == "whoami":
                return handle_whoami(admin)
            if action == "permissions":
                return handle_get_permissions(admin, vhost, user)

    def _register_mutative(self):
        @self.mcp.tool()
        def manage_queue(
            action: Literal["create", "delete", "purge"],
            name: str,
            vhost: str = "/",
            queue_type: str = "quorum",
            durable: bool = True,
            arguments: dict | None = None,
        ) -> str:
            """Create, delete, or purge a queue. queue_type: quorum (default), classic, stream."""
            admin = self._get_admin()
            validate_rabbitmq_name(name, "Queue name")
            if action == "create":
                handle_create_queue(admin, name, vhost, queue_type, durable, False, arguments)
                return f"Queue {name} created ({queue_type})"
            if action == "delete":
                handle_delete_queue(admin, name, vhost)
                return f"Queue {name} deleted"
            if action == "purge":
                handle_purge_queue(admin, name, vhost)
                return f"Queue {name} purged"

        @self.mcp.tool()
        def manage_exchange(
            action: Literal["create", "delete"],
            name: str,
            exchange_type: str = "direct",
            vhost: str = "/",
            durable: bool = True,
            arguments: dict | None = None,
        ) -> str:
            """Create or delete an exchange. exchange_type: direct, fanout, topic, headers."""
            admin = self._get_admin()
            validate_rabbitmq_name(name, "Exchange name")
            if action == "create":
                handle_create_exchange(admin, name, exchange_type, vhost, durable, False, arguments)
                return f"Exchange {name} created ({exchange_type})"
            if action == "delete":
                handle_delete_exchange(admin, name, vhost)
                return f"Exchange {name} deleted"

        @self.mcp.tool()
        def manage_binding(
            action: Literal["create", "delete"],
            exchange: str,
            queue: str,
            routing_key: str = "",
            vhost: str = "/",
            props_key: str | None = None,
            arguments: dict | None = None,
        ) -> str:
            """Create or delete a binding. For delete, props_key from bindings list is required."""
            admin = self._get_admin()
            if action == "create":
                handle_create_binding(admin, exchange, queue, vhost, routing_key, arguments)
                return f"Binding: {exchange} -> {queue}"
            if action == "delete":
                if not props_key:
                    raise ValueError("props_key required for delete")
                handle_delete_binding(admin, exchange, queue, props_key, vhost)
                return f"Binding deleted: {exchange} -> {queue}"

        @self.mcp.tool()
        def manage_policy(
            action: Literal["create", "delete"],
            name: str,
            pattern: str = ".*",
            definition: dict | None = None,
            vhost: str = "/",
            priority: int = 0,
            apply_to: str = "all",
        ) -> str:
            """Create or delete a policy. definition: e.g. {'max-length': 1000}. apply_to: all, queues, exchanges."""
            admin = self._get_admin()
            if action == "create":
                if not definition:
                    raise ValueError("definition required for create")
                handle_create_policy(admin, name, pattern, definition, vhost, priority, apply_to)
                return f"Policy {name} created"
            if action == "delete":
                handle_delete_policy(admin, name, vhost)
                return f"Policy {name} deleted"

        @self.mcp.tool()
        def manage_vhost(
            action: Literal["create", "delete"],
            name: str,
        ) -> str:
            """Create or delete a virtual host."""
            admin = self._get_admin()
            if action == "create":
                handle_create_vhost(admin, name)
                return f"Vhost {name} created"
            if action == "delete":
                handle_delete_vhost(admin, name)
                return f"Vhost {name} deleted"

        @self.mcp.tool()
        def publish(
            method: Literal["amqp_queue", "amqp_fanout", "http"],
            target: str,
            message: str,
            routing_key: str = "",
            vhost: str = "/",
            properties: dict | None = None,
        ) -> str:
            """Publish a message. amqp_queue: direct to queue. amqp_fanout: to fanout exchange. http: via Management API."""
            if method == "amqp_queue":
                handle_enqueue(self._get_rmq(), target, message)
                return f"Published to queue {target}"
            if method == "amqp_fanout":
                handle_fanout(self._get_rmq(), target, message)
                return f"Published to fanout {target}"
            if method == "http":
                result = handle_publish_message(self._get_admin(), target, routing_key, message, vhost, properties)
                return f"Published via HTTP: {result}"

        @self.mcp.tool()
        def close_connection(name: str) -> str:
            """Close a connection by name."""
            if not name:
                raise ValueError("name required")
            admin = self._get_admin()
            handle_close_connection(admin, name)
            return "Connection closed"

        @self.mcp.tool()
        def set_permissions(
            vhost: str = "/",
            user: str = "guest",
            configure: str = ".*",
            write: str = ".*",
            read: str = ".*",
        ) -> str:
            """Set permissions for a user in a vhost. configure/write/read are regex patterns."""
            admin = self._get_admin()
            handle_set_permissions(admin, vhost, user, configure, write, read)
            return f"Permissions set for {user} in {vhost}"

        @self.mcp.tool()
        def rebalance_queues() -> str:
            """Rebalance queue leaders across cluster nodes."""
            admin = self._get_admin()
            handle_rebalance_queues(admin)
            return "Rebalance initiated"

    def _register_migration(self):
        @self.mcp.tool()
        def definitions_export(transforms: list[str] | None = None) -> dict:
            """Export definitions with optional transforms: strip_cmq_keys, drop_empty_policies, convert_classic_to_quorum, obfuscate_credentials, exclude_users, exclude_permissions."""
            return handle_export_definitions(self._get_admin(), transforms)

        @self.mcp.tool()
        def definitions_import(
            definitions: dict,
            partial: bool = False,
        ) -> str:
            """Import definitions to active broker. partial=False (default): full merge import. partial=True: upload a partial definition snippet (queues, exchanges, etc)."""
            admin = self._get_admin()
            if partial:
                handle_update_definition(admin, definitions)
                return "Updated (partial)"
            handle_import_definitions(admin, definitions)
            return "Imported"

        @self.mcp.tool()
        def definitions_compare(source_alias: str, target_alias: str) -> dict:
            """Compare definitions between two brokers. Shows missing/extra items."""
            for alias in (source_alias, target_alias):
                if alias not in self.brokers:
                    raise ValueError(f"Unknown alias '{alias}'")
            defs_a = self.brokers[source_alias]["rmq_admin"].get_broker_definition()
            defs_b = self.brokers[target_alias]["rmq_admin"].get_broker_definition()
            return handle_compare_definitions(defs_a, defs_b)

        @self.mcp.tool()
        def definitions_migrate(
            source_alias: str, target_alias: str, transforms: list[str] | None = None
        ) -> str:
            """Export from source, transform, import to target. Core blue-green migration."""
            for alias in (source_alias, target_alias):
                if alias not in self.brokers:
                    raise ValueError(f"Unknown alias '{alias}'")
            defs = handle_export_definitions(self.brokers[source_alias]["rmq_admin"], transforms)
            handle_import_definitions(self.brokers[target_alias]["rmq_admin"], defs)
            return f"Migrated from '{source_alias}' to '{target_alias}'"

        @self.mcp.tool()
        def migration_readiness(source_alias: str, target_alias: str) -> dict:
            """Pre-flight check: both connected, no alarms, topology match."""
            return handle_check_migration_readiness(self.brokers, source_alias, target_alias)

        @self.mcp.tool()
        def federation_setup(
            upstream_name: str, upstream_uri: str, vhost: str = "/", policy_pattern: str = ".*"
        ) -> dict:
            """Set up federation upstream and policy for message draining."""
            return handle_setup_federation(self._get_admin(), upstream_name, upstream_uri, vhost, policy_pattern)

    def _register_observability(self):
        @self.mcp.tool()
        def find_queues(
            min_depth: int | None = None,
            min_idle_seconds: int | None = None,
            no_consumers: bool = False,
            min_unacked: int | None = None,
            vhost: str = "/",
        ) -> list[dict]:
            """Find queues by threshold: depth, idle time, no consumers, unacked count."""
            return handle_find_queues_by_threshold(self._get_admin(), min_depth, min_idle_seconds, no_consumers, min_unacked, vhost)

    def _register_health(self):
        @self.mcp.tool()
        def health(
            check: Literal["alarms", "quorum", "certificates", "protocol", "vhosts", "features", "deprecated"],
            protocol: str | None = None,
            within: int = 30,
            unit: str = "days",
        ) -> Any:
            """Health checks. alarms: local alarms. quorum: quorum critical. certificates: TLS expiry. protocol: listener active. vhosts: vhost health. features: feature flags. deprecated: deprecated features in use."""
            admin = self._get_admin()
            if check == "alarms":
                return handle_check_local_alarms(admin)
            if check == "quorum":
                return handle_is_node_in_quorum_critical(admin)
            if check == "certificates":
                return handle_check_certificate_expiration(admin, within, unit)
            if check == "protocol":
                if not protocol:
                    raise ValueError("protocol required (amqp, mqtt, stomp, stream, http)")
                return handle_check_protocol_listener(admin, protocol)
            if check == "vhosts":
                return handle_check_virtual_hosts(admin)
            if check == "features":
                return handle_list_feature_flags(admin)
            if check == "deprecated":
                return handle_list_deprecated_features(admin)
