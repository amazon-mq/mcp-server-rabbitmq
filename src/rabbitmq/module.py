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
# This file is part of the awslabs namespace.
# It is intentionally minimal to support PEP 420 namespace packages.

from typing import Any

from mcp.server.fastmcp import FastMCP

from .admin import RabbitMQAdmin
from .connection import RabbitMQConnection, validate_rabbitmq_name
from .handlers import (
    handle_check_migration_readiness,
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
    handle_get_bindings,
    handle_get_cluster_nodes,
    handle_get_definition,
    handle_get_exchange_info,
    handle_get_guidelines,
    handle_get_messages,
    handle_get_node_information,
    handle_get_permissions,
    handle_get_policy,
    handle_get_queue_info,
    handle_import_definitions,
    handle_is_broker_in_alarm,
    handle_is_node_in_quorum_critical,
    handle_list_channels,
    handle_list_connections,
    handle_list_consumers,
    handle_list_exchanges,
    handle_list_policies,
    handle_list_queues,
    handle_list_shovels,
    handle_list_users,
    handle_list_vhosts,
    handle_publish_message,
    handle_purge_queue,
    handle_set_permissions,
    handle_setup_federation,
    handle_shovel,
    handle_update_definition,
)


class RabbitMQModule:
    """A module that contains RabbitMQ API."""

    def __init__(self, mcp: FastMCP):
        """Initialize the RabbitMQ module."""
        self.mcp = mcp
        self.brokers: dict[str, dict] = {}
        self.active_alias: str | None = None

    def _get_admin(self) -> RabbitMQAdmin:
        """Return the active broker's admin client."""
        if not self.active_alias or self.active_alias not in self.brokers:
            raise AssertionError("No active broker. Call initialize_connection first.")
        return self.brokers[self.active_alias]["rmq_admin"]

    def _get_rmq(self) -> RabbitMQConnection:
        """Return the active broker's AMQP connection."""
        if not self.active_alias or self.active_alias not in self.brokers:
            raise AssertionError("No active broker. Call initialize_connection first.")
        return self.brokers[self.active_alias]["rmq"]

    def register_rabbitmq_management_tools(self, allow_mutative_tools: bool = False):
        """Install RabbitMQ tools to the MCP server."""
        self.__register_critical_tools()
        self.__register_read_only_tools()
        if allow_mutative_tools:
            self.__register_mutative_tools()

    def __register_critical_tools(self):
        @self.mcp.tool()
        def rabbitmq_broker_initialize_connection(
            broker_hostname: str,
            username: str,
            password: str,
            port: int = 5671,
            use_tls: bool = True,
            alias: str | None = None,
        ) -> str:
            """Connect to a new RabbitMQ broker which authentication strategy is SIMPLE.

            broker_hostname: The hostname of the broker.
            username: The username of user
            password: The password of user
            alias: Optional name for this connection (default: hostname). Use to manage multiple brokers, e.g. 'blue', 'green', 'prod'.
            """
            alias = alias or broker_hostname
            rmq = RabbitMQConnection(
                hostname=broker_hostname,
                username=username,
                password=password,
                port=port,
                use_tls=use_tls,
            )
            rmq_admin = RabbitMQAdmin(
                hostname=broker_hostname,
                username=username,
                password=password,
                use_tls=use_tls,
            )
            rmq_admin.test_connection()
            self.brokers[alias] = {
                "rmq": rmq,
                "rmq_admin": rmq_admin,
                "hostname": broker_hostname,
            }
            self.active_alias = alias
            return f"Connected to {broker_hostname} as '{alias}' (active)"

        @self.mcp.tool()
        def rabbitmq_broker_initialize_connection_with_oauth(
            broker_hostname: str,
            oauth_token: str,
            alias: str | None = None,
        ) -> str:
            """Connect to a new RabbitMQ broker using OAuth.

            broker_hostname: The hostname of the broker.
            oauth_token: A valid access token
            alias: Optional name for this connection (default: hostname).
            """
            alias = alias or broker_hostname
            rmq = RabbitMQConnection(
                hostname=broker_hostname,
                username="",
                password=oauth_token,
            )
            rmq_admin = RabbitMQAdmin(
                hostname=broker_hostname,
                username="",
                password=oauth_token,
            )
            rmq_admin.test_connection()
            self.brokers[alias] = {
                "rmq": rmq,
                "rmq_admin": rmq_admin,
                "hostname": broker_hostname,
            }
            self.active_alias = alias
            return f"Connected to {broker_hostname} as '{alias}' (active)"

        @self.mcp.tool()
        def rabbitmq_broker_select(alias: str) -> str:
            """Switch the active broker by alias. All subsequent tool calls will target this broker."""
            if alias not in self.brokers:
                available = ", ".join(self.brokers.keys()) or "(none)"
                raise ValueError(f"Unknown alias '{alias}'. Available: {available}")
            self.active_alias = alias
            hostname = self.brokers[alias]["hostname"]
            return f"Active broker: '{alias}' ({hostname})"

        @self.mcp.tool()
        def rabbitmq_broker_list_registered_brokers() -> list[dict]:
            """List all registered broker connections and which is active."""
            return [
                {
                    "alias": alias,
                    "hostname": info["hostname"],
                    "active": alias == self.active_alias,
                }
                for alias, info in self.brokers.items()
            ]

        @self.mcp.tool()
        def rabbitmq_broker_get_guideline(guideline_name: str) -> str:
            """Get the general best practices for deploying RabbitMQ on Amazon MQ.

            - guideline_name: It can take the following value:
                - rabbitmq_broker_sizing_guide: this guide tells the customer what instance size to pick for production workload
                - rabbitmq_broker_setup_best_practices_guide: this guide tells the customer what are the best practices in setting up the RabbitMQ broker
                - rabbitmq_quorum_queue_migration_guide: this guide tells the customer how to migrate from classic mirror queue to quorum queue
                - rabbitmq_client_performance_optimization_guide: this guide tells the customer how to optimize their application to get performance gain of using RabbitMQ
                - rabbitmq_production_deployment_guidelines: this guide covers production deployment requirements including hardware, storage, security, and networking
            """
            result = handle_get_guidelines(guideline_name)
            return str(result)

    def __register_read_only_tools(self):
        @self.mcp.tool()
        def rabbitmq_broker_list_queues() -> list[Any]:
            """List all the queues in the broker."""
            return handle_list_queues(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_list_exchanges() -> list[Any]:
            """List all the exchanges in the broker."""
            return handle_list_exchanges(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_list_vhosts() -> list[Any]:
            """List all the virtual hosts (vhosts) in the broker."""
            return handle_list_vhosts(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_get_queue_info(queue: str, vhost: str = "/") -> dict:
            """Get detailed information about a specific queue."""
            validate_rabbitmq_name(queue, "Queue name")
            return handle_get_queue_info(self._get_admin(), queue, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_exchange_info(exchange: str, vhost: str = "/") -> dict:
            """Get detailed information about a specific exchange."""
            validate_rabbitmq_name(exchange, "Exchange name")
            return handle_get_exchange_info(self._get_admin(), exchange, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_list_shovels() -> list[Any]:
            """Get detailed information about shovels in the RabbitMQ broker."""
            return handle_list_shovels(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_get_shovel_info(name: str, vhost: str = "/") -> dict:
            """Get detailed information about specific shovel by name that is in a selected virtual host (vhost) in the RabbitMQ broker."""
            return handle_shovel(self._get_admin(), name, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_cluster_nodes_info() -> list[Any]:
            """Get the list of nodes and their info in the cluster."""
            return handle_get_cluster_nodes(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_list_connections() -> list[Any]:
            """List all connections on the RabbitMQ broker."""
            return handle_list_connections(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_list_consumers() -> list[Any]:
            """List all consumers on the RabbitMQ broker."""
            return handle_list_consumers(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_list_users() -> list[Any]:
            """List all users on the RabbitMQ broker."""
            return handle_list_users(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_is_in_alarm() -> bool:
            """Check if the RabbitMQ broker is in alarm."""
            return handle_is_broker_in_alarm(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_is_quorum_critical() -> bool:
            """Check if there are quorum queues with minimum online quorum."""
            return handle_is_node_in_quorum_critical(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_get_broker_definition() -> dict:
            """Get the RabbitMQ definitions: exchanges, queues, bindings, users, virtual hosts, permissions, topic permissions, and parameters. Everything apart from messages."""
            return handle_get_definition(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_get_bindings(
            queue: str | None = None, exchange: str | None = None, vhost: str = "/"
        ) -> list[dict]:
            """Get bindings, optionally filtered by queue or exchange. If neither is specified, returns all bindings in the vhost."""
            return handle_get_bindings(
                self._get_admin(), queue=queue, exchange=exchange, vhost=vhost
            )

        @self.mcp.tool()
        def rabbitmq_broker_get_node_information(node_name: str) -> dict:
            """Get detailed information about a specific node in the cluster including memory, disk, uptime, and runtime details."""
            return handle_get_node_information(self._get_admin(), node_name)

        @self.mcp.tool()
        def rabbitmq_broker_list_policies(vhost: str = "/") -> list[dict]:
            """List all policies in a virtual host."""
            return handle_list_policies(self._get_admin(), vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_policy(name: str, vhost: str = "/") -> dict:
            """Get a specific policy by name."""
            return handle_get_policy(self._get_admin(), name, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_messages(
            queue: str, vhost: str = "/", count: int = 1, ackmode: str = "ack_requeue_true"
        ) -> list[dict]:
            """Peek at messages in a queue without consuming them. Messages are requeued by default.

            ackmode: ack_requeue_true (peek, default), ack_requeue_false (consume)
            """
            return handle_get_messages(self._get_admin(), queue, vhost, count, ackmode)

        @self.mcp.tool()
        def rabbitmq_broker_list_channels() -> list[dict]:
            """List all open channels on the broker."""
            return handle_list_channels(self._get_admin())

        @self.mcp.tool()
        def rabbitmq_broker_get_permissions(vhost: str, user: str) -> dict:
            """Get permissions for a user in a virtual host."""
            return handle_get_permissions(self._get_admin(), vhost, user)

        @self.mcp.tool()
        def rabbitmq_broker_compare_definitions(source_alias: str, target_alias: str) -> dict:
            """Compare definitions between two connected brokers. Returns missing/extra items per section (queues, exchanges, bindings, policies, vhosts)."""
            for alias in (source_alias, target_alias):
                if alias not in self.brokers:
                    raise ValueError(f"Unknown alias '{alias}'")
            defs_a = self.brokers[source_alias]["rmq_admin"].get_broker_definition()
            defs_b = self.brokers[target_alias]["rmq_admin"].get_broker_definition()
            return handle_compare_definitions(defs_a, defs_b)

        @self.mcp.tool()
        def rabbitmq_broker_check_migration_readiness(
            source_alias: str, target_alias: str
        ) -> dict:
            """Pre-flight check for blue-green migration. Verifies both brokers connected, no alarms, and topology match."""
            return handle_check_migration_readiness(self.brokers, source_alias, target_alias)

    def __register_mutative_tools(self):
        @self.mcp.tool()
        def rabbitmq_broker_delete_queue(queue: str, vhost: str = "/") -> str:
            """Delete a specific queue."""
            validate_rabbitmq_name(queue, "Queue name")
            handle_delete_queue(self._get_admin(), queue, vhost)
            return f"Queue {queue} successfully deleted"

        @self.mcp.tool()
        def rabbitmq_broker_purge_queue(queue: str, vhost: str = "/") -> str:
            """Remove all messages from a specific queue."""
            validate_rabbitmq_name(queue, "Queue name")
            handle_purge_queue(self._get_admin(), queue, vhost)
            return f"Queue {queue} successfully purged"

        @self.mcp.tool()
        def rabbitmq_broker_delete_exchange(exchange: str, vhost: str = "/") -> str:
            """Delete a specific exchange."""
            validate_rabbitmq_name(exchange, "Exchange name")
            handle_delete_exchange(self._get_admin(), exchange, vhost)
            return f"Exchange {exchange} successfully deleted"

        @self.mcp.tool()
        def rabbitmq_broker_update_definition(server_definition: dict) -> str:
            """Update The server definitions: exchanges, queues, bindings, users, virtual hosts, permissions, topic permissions, and parameters. Everything apart from messages."""
            handle_update_definition(self._get_admin(), server_definition)
            return "Updated successfully"

        @self.mcp.tool()
        def rabbitmq_broker_enqueue(queue: str, message: str) -> str:
            """Publish a message to a specific queue via AMQP. The queue will be declared if it does not exist."""
            handle_enqueue(self._get_rmq(), queue, message)
            return f"Message published to queue {queue}"

        @self.mcp.tool()
        def rabbitmq_broker_fanout(exchange: str, message: str) -> str:
            """Publish a message to a fanout exchange via AMQP. The exchange will be declared if it does not exist."""
            handle_fanout(self._get_rmq(), exchange, message)
            return f"Message published to fanout exchange {exchange}"

        @self.mcp.tool()
        def rabbitmq_broker_create_queue(
            queue: str,
            vhost: str = "/",
            queue_type: str = "quorum",
            durable: bool = True,
            auto_delete: bool = False,
            arguments: dict | None = None,
        ) -> str:
            """Create a queue.

            queue_type: quorum (default, recommended), classic, or stream
            """
            handle_create_queue(
                self._get_admin(), queue, vhost, queue_type, durable, auto_delete, arguments
            )
            return f"Queue {queue} created"

        @self.mcp.tool()
        def rabbitmq_broker_create_exchange(
            exchange: str,
            exchange_type: str = "direct",
            vhost: str = "/",
            durable: bool = True,
            auto_delete: bool = False,
            arguments: dict | None = None,
        ) -> str:
            """Create an exchange.

            exchange_type: direct, fanout, topic, or headers
            """
            handle_create_exchange(
                self._get_admin(), exchange, exchange_type, vhost, durable, auto_delete, arguments
            )
            return f"Exchange {exchange} created"

        @self.mcp.tool()
        def rabbitmq_broker_create_binding(
            exchange: str,
            queue: str,
            vhost: str = "/",
            routing_key: str = "",
            arguments: dict | None = None,
        ) -> str:
            """Create a binding from an exchange to a queue."""
            handle_create_binding(
                self._get_admin(), exchange, queue, vhost, routing_key, arguments
            )
            return f"Binding created: {exchange} -> {queue}"

        @self.mcp.tool()
        def rabbitmq_broker_delete_binding(
            exchange: str, queue: str, props_key: str, vhost: str = "/"
        ) -> str:
            """Delete a binding. The props_key can be found from get_bindings."""
            handle_delete_binding(self._get_admin(), exchange, queue, props_key, vhost)
            return f"Binding deleted: {exchange} -> {queue}"

        @self.mcp.tool()
        def rabbitmq_broker_create_policy(
            name: str,
            pattern: str,
            definition: dict,
            vhost: str = "/",
            priority: int = 0,
            apply_to: str = "all",
        ) -> str:
            """Create or update a policy.

            pattern: regex matching queue/exchange names (e.g. '.*' for all)
            definition: policy settings (e.g. {'ha-mode': 'all'}, {'max-length': 1000})
            apply_to: all, queues, exchanges, or classic_queues
            """
            handle_create_policy(
                self._get_admin(), name, pattern, definition, vhost, priority, apply_to
            )
            return f"Policy {name} created"

        @self.mcp.tool()
        def rabbitmq_broker_delete_policy(name: str, vhost: str = "/") -> str:
            """Delete a policy."""
            handle_delete_policy(self._get_admin(), name, vhost)
            return f"Policy {name} deleted"

        @self.mcp.tool()
        def rabbitmq_broker_publish_message(
            exchange: str,
            routing_key: str,
            payload: str,
            vhost: str = "/",
            properties: dict | None = None,
        ) -> dict:
            """Publish a message via the HTTP Management API. Use for diagnostics — for production publishing, use AMQP (enqueue/fanout tools)."""
            return handle_publish_message(
                self._get_admin(), exchange, routing_key, payload, vhost, properties
            )

        @self.mcp.tool()
        def rabbitmq_broker_close_connection(name: str) -> str:
            """Close a specific connection by name. Get connection names from list_connections."""
            handle_close_connection(self._get_admin(), name)
            return f"Connection {name} closed"

        @self.mcp.tool()
        def rabbitmq_broker_create_vhost(name: str) -> str:
            """Create a virtual host."""
            handle_create_vhost(self._get_admin(), name)
            return f"Vhost {name} created"

        @self.mcp.tool()
        def rabbitmq_broker_delete_vhost(name: str) -> str:
            """Delete a virtual host. WARNING: this deletes all queues, exchanges, bindings, and permissions in the vhost."""
            handle_delete_vhost(self._get_admin(), name)
            return f"Vhost {name} deleted"

        @self.mcp.tool()
        def rabbitmq_broker_set_permissions(
            vhost: str,
            user: str,
            configure: str = ".*",
            write: str = ".*",
            read: str = ".*",
        ) -> str:
            """Set permissions for a user in a virtual host.

            configure/write/read: regex patterns for allowed resource names (default '.*' = all)
            """
            handle_set_permissions(self._get_admin(), vhost, user, configure, write, read)
            return f"Permissions set for {user} in {vhost}"

        @self.mcp.tool()
        def rabbitmq_broker_export_definitions(
            transforms: list[str] | None = None,
        ) -> dict:
            """Export definitions from the active broker with optional transformations.

            transforms: list of transformation names to apply. Available:
                - strip_cmq_keys: remove classic mirrored queue HA keys from policies
                - drop_empty_policies: remove policies with empty definitions
                - convert_classic_to_quorum: change classic queues to quorum type
                - obfuscate_credentials: replace usernames/passwords with dummy values
                - exclude_users: remove users section
                - exclude_permissions: remove permissions sections
            """
            return handle_export_definitions(self._get_admin(), transforms)

        @self.mcp.tool()
        def rabbitmq_broker_import_definitions(definitions: dict) -> str:
            """Import definitions to the active broker. Merges with existing definitions (RabbitMQ default behavior)."""
            handle_import_definitions(self._get_admin(), definitions)
            return "Definitions imported successfully"

        @self.mcp.tool()
        def rabbitmq_broker_migrate_definitions(
            source_alias: str,
            target_alias: str,
            transforms: list[str] | None = None,
        ) -> str:
            """Export definitions from source broker, apply transformations, and import to target broker. The core blue-green migration primitive."""
            for alias in (source_alias, target_alias):
                if alias not in self.brokers:
                    raise ValueError(f"Unknown alias '{alias}'")
            source_admin = self.brokers[source_alias]["rmq_admin"]
            target_admin = self.brokers[target_alias]["rmq_admin"]
            defs = handle_export_definitions(source_admin, transforms)
            handle_import_definitions(target_admin, defs)
            return f"Definitions migrated from '{source_alias}' to '{target_alias}'"

        @self.mcp.tool()
        def rabbitmq_broker_setup_federation(
            upstream_name: str,
            upstream_uri: str,
            vhost: str = "/",
            policy_pattern: str = ".*",
        ) -> dict:
            """Set up federation upstream and policy on the active broker. Creates a bridge for message draining from the upstream broker. Checks that the federation plugin is enabled first."""
            return handle_setup_federation(
                self._get_admin(), upstream_name, upstream_uri, vhost, policy_pattern
            )
