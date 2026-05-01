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
    handle_close_connection,
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
    handle_shovel,
    handle_update_definition,
)


class RabbitMQModule:
    """A module that contains RabbitMQ API."""

    def __init__(self, mcp: FastMCP):
        """Initialize the RabbitMQ module."""
        self.mcp = mcp
        self.rmq: RabbitMQConnection | None = None
        self.rmq_admin: RabbitMQAdmin | None = None

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
        ) -> str:
            """Connect to a new RabbitMQ broker which authentication strategy is SIMPLE.

            broker_hostname: The hostname of the broker. For example, b-a9565a64-da39-4afc-9239-c43a9376b5ba.mq.us-east-1.on.aws, b-9560b8e1-3d33-4d91-9488-a3dc4a61dfe7.mq.us-east-1.amazonaws.com
            username: The username of user
            password: The password of user
            """
            self.rmq = RabbitMQConnection(
                hostname=broker_hostname,
                username=username,
                password=password,
                port=port,
                use_tls=use_tls,
            )
            self.rmq_admin = RabbitMQAdmin(
                hostname=broker_hostname,
                username=username,
                password=password,
                use_tls=use_tls,
            )
            self.rmq_admin.test_connection()
            return "successfully connected"

        @self.mcp.tool()
        def rabbitmq_broker_initialize_connection_with_oauth(
            broker_hostname: str,
            oauth_token: str,
        ) -> str:
            """Connect to a new RabbitMQ broker using OAuth. It only applies to RabbitMQ broker which authentication strategy is config_managed.

            broker_hostname: The hostname of the broker. For example, b-a9565a64-da39-4afc-9239-c43a9376b5ba.mq.us-east-1.on.aws, b-9560b8e1-3d33-4d91-9488-a3dc4a61dfe7.mq.us-east-1.amazonaws.com
            oauth_token: A valid access token
            """
            self.rmq = RabbitMQConnection(
                hostname=broker_hostname,
                username="",
                password=oauth_token,
            )
            self.rmq_admin = RabbitMQAdmin(
                hostname=broker_hostname,
                username="",
                password=oauth_token,
            )
            self.rmq_admin.test_connection()
            return "successfully connected"

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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_queues(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_list_exchanges() -> list[Any]:
            """List all the exchanges in the broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_exchanges(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_list_vhosts() -> list[Any]:
            """List all the virtual hosts (vhosts) in the broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_vhosts(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_get_queue_info(queue: str, vhost: str = "/") -> dict:
            """Get detailed information about a specific queue."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            validate_rabbitmq_name(queue, "Queue name")
            return handle_get_queue_info(self.rmq_admin, queue, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_exchange_info(exchange: str, vhost: str = "/") -> dict:
            """Get detailed information about a specific exchange."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            validate_rabbitmq_name(exchange, "Exchange name")
            return handle_get_exchange_info(self.rmq_admin, exchange, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_list_shovels() -> list[Any]:
            """Get detailed information about shovels in the RabbitMQ broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_shovels(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_get_shovel_info(name: str, vhost: str = "/") -> dict:
            """Get detailed information about specific shovel by name that is in a selected virtual host (vhost) in the RabbitMQ broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_shovel(self.rmq_admin, name, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_cluster_nodes_info() -> list[Any]:
            """Get the list of nodes and their info in the cluster."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_cluster_nodes(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_list_connections() -> list[Any]:
            """List all connections on the RabbitMQ broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_connections(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_list_consumers() -> list[Any]:
            """List all consumers on the RabbitMQ broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_consumers(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_list_users() -> list[Any]:
            """List all users on the RabbitMQ broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_users(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_is_in_alarm() -> bool:
            """Check if the RabbitMQ broker is in alarm."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_is_broker_in_alarm(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_is_quorum_critical() -> bool:
            """Check if there are quorum queues with minimum online quorum."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_is_node_in_quorum_critical(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_get_broker_definition() -> dict:
            """Get the RabbitMQ definitions: exchanges, queues, bindings, users, virtual hosts, permissions, topic permissions, and parameters. Everything apart from messages."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_definition(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_get_bindings(
            queue: str | None = None, exchange: str | None = None, vhost: str = "/"
        ) -> list[dict]:
            """Get bindings, optionally filtered by queue or exchange. If neither is specified, returns all bindings in the vhost."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_bindings(self.rmq_admin, queue=queue, exchange=exchange, vhost=vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_node_information(node_name: str) -> dict:
            """Get detailed information about a specific node in the cluster including memory, disk, uptime, and runtime details."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_node_information(self.rmq_admin, node_name)

        @self.mcp.tool()
        def rabbitmq_broker_list_policies(vhost: str = "/") -> list[dict]:
            """List all policies in a virtual host."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_policies(self.rmq_admin, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_policy(name: str, vhost: str = "/") -> dict:
            """Get a specific policy by name."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_policy(self.rmq_admin, name, vhost)

        @self.mcp.tool()
        def rabbitmq_broker_get_messages(
            queue: str, vhost: str = "/", count: int = 1, ackmode: str = "ack_requeue_true"
        ) -> list[dict]:
            """Peek at messages in a queue without consuming them. Messages are requeued by default.

            ackmode: ack_requeue_true (peek, default), ack_requeue_false (consume)
            """
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_messages(self.rmq_admin, queue, vhost, count, ackmode)

        @self.mcp.tool()
        def rabbitmq_broker_list_channels() -> list[dict]:
            """List all open channels on the broker."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_list_channels(self.rmq_admin)

        @self.mcp.tool()
        def rabbitmq_broker_get_permissions(vhost: str, user: str) -> dict:
            """Get permissions for a user in a virtual host."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_get_permissions(self.rmq_admin, vhost, user)

    def __register_mutative_tools(self):
        @self.mcp.tool()
        def rabbitmq_broker_delete_queue(queue: str, vhost: str = "/") -> str:
            """Delete a specific queue."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            validate_rabbitmq_name(queue, "Queue name")
            handle_delete_queue(self.rmq_admin, queue, vhost)
            return f"Queue {queue} successfully deleted"

        @self.mcp.tool()
        def rabbitmq_broker_purge_queue(queue: str, vhost: str = "/") -> str:
            """Remove all messages from a specific queue."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            validate_rabbitmq_name(queue, "Queue name")
            handle_purge_queue(self.rmq_admin, queue, vhost)
            return f"Queue {queue} successfully purged"

        @self.mcp.tool()
        def rabbitmq_broker_delete_exchange(exchange: str, vhost: str = "/") -> str:
            """Delete a specific exchange."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            validate_rabbitmq_name(exchange, "Exchange name")
            handle_delete_exchange(self.rmq_admin, exchange, vhost)
            return f"Exchange {exchange} successfully deleted"

        @self.mcp.tool()
        def rabbitmq_broker_update_definition(server_definition: dict) -> str:
            """Update The server definitions: exchanges, queues, bindings, users, virtual hosts, permissions, topic permissions, and parameters. Everything apart from messages."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_update_definition(self.rmq_admin, server_definition)
            return "Updated successfully"

        @self.mcp.tool()
        def rabbitmq_broker_enqueue(queue: str, message: str) -> str:
            """Publish a message to a specific queue via AMQP. The queue will be declared if it does not exist."""
            if self.rmq is None:
                raise AssertionError("RabbitMQ AMQP connection not established.")
            handle_enqueue(self.rmq, queue, message)
            return f"Message published to queue {queue}"

        @self.mcp.tool()
        def rabbitmq_broker_fanout(exchange: str, message: str) -> str:
            """Publish a message to a fanout exchange via AMQP. The exchange will be declared if it does not exist."""
            if self.rmq is None:
                raise AssertionError("RabbitMQ AMQP connection not established.")
            handle_fanout(self.rmq, exchange, message)
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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_create_queue(
                self.rmq_admin, queue, vhost, queue_type, durable, auto_delete, arguments
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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_create_exchange(
                self.rmq_admin, exchange, exchange_type, vhost, durable, auto_delete, arguments
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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_create_binding(self.rmq_admin, exchange, queue, vhost, routing_key, arguments)
            return f"Binding created: {exchange} -> {queue}"

        @self.mcp.tool()
        def rabbitmq_broker_delete_binding(
            exchange: str, queue: str, props_key: str, vhost: str = "/"
        ) -> str:
            """Delete a binding. The props_key can be found from get_bindings."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_delete_binding(self.rmq_admin, exchange, queue, props_key, vhost)
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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_create_policy(
                self.rmq_admin, name, pattern, definition, vhost, priority, apply_to
            )
            return f"Policy {name} created"

        @self.mcp.tool()
        def rabbitmq_broker_delete_policy(name: str, vhost: str = "/") -> str:
            """Delete a policy."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_delete_policy(self.rmq_admin, name, vhost)
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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            return handle_publish_message(
                self.rmq_admin, exchange, routing_key, payload, vhost, properties
            )

        @self.mcp.tool()
        def rabbitmq_broker_close_connection(name: str) -> str:
            """Close a specific connection by name. Get connection names from list_connections."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_close_connection(self.rmq_admin, name)
            return f"Connection {name} closed"

        @self.mcp.tool()
        def rabbitmq_broker_create_vhost(name: str) -> str:
            """Create a virtual host."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_create_vhost(self.rmq_admin, name)
            return f"Vhost {name} created"

        @self.mcp.tool()
        def rabbitmq_broker_delete_vhost(name: str) -> str:
            """Delete a virtual host. WARNING: this deletes all queues, exchanges, bindings, and permissions in the vhost."""
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_delete_vhost(self.rmq_admin, name)
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
            if self.rmq_admin is None:
                raise AssertionError("RabbitMQ admin endpoints not connected.")
            handle_set_permissions(self.rmq_admin, vhost, user, configure, write, read)
            return f"Permissions set for {user} in {vhost}"
