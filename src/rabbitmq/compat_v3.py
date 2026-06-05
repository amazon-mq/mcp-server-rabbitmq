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

"""v3 compatibility layer: registers old tool names as thin wrappers around v4 dispatchers."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .module_v4 import RabbitMQModuleV4


def register_v3_compat_tools(mcp: FastMCP, module: RabbitMQModuleV4) -> None:
    """Register deprecated v3 tool names that delegate to v4 dispatcher logic.

    These wrappers exist solely for backward compatibility with clients that
    reference old tool names in their configurations. Each wrapper logs a
    deprecation notice and delegates to the corresponding v4 handler.
    """

    @mcp.tool()
    def rabbitmq_broker_list_queues(vhost: str = "/") -> Any:
        """DEPRECATED: use queues(action='list') instead. List all queues."""
        from .handlers import handle_list_queues_by_vhost

        return handle_list_queues_by_vhost(module._get_admin(), vhost)

    @mcp.tool()
    def rabbitmq_broker_list_exchanges(vhost: str = "/") -> Any:
        """DEPRECATED: use exchanges(action='list') instead. List all exchanges."""
        from .handlers import handle_list_exchanges_by_vhost

        return handle_list_exchanges_by_vhost(module._get_admin(), vhost)

    @mcp.tool()
    def rabbitmq_broker_get_queue_info(name: str, vhost: str = "/") -> Any:
        """DEPRECATED: use queues(action='info', name=..., vhost=...) instead. Get queue details."""
        from .handlers import handle_get_queue_info

        return handle_get_queue_info(module._get_admin(), name, vhost)

    @mcp.tool()
    def rabbitmq_broker_get_exchange_info(name: str, vhost: str = "/") -> Any:
        """DEPRECATED: use exchanges(action='info', name=..., vhost=...) instead. Get exchange details."""
        from .handlers import handle_get_exchange_info

        return handle_get_exchange_info(module._get_admin(), name, vhost)

    @mcp.tool()
    def rabbitmq_broker_list_connections() -> Any:
        """DEPRECATED: use connections(action='list') instead. List all connections."""
        from .handlers import handle_list_connections

        return handle_list_connections(module._get_admin())

    @mcp.tool()
    def rabbitmq_broker_get_overview() -> Any:
        """DEPRECATED: use overview() instead. Get broker overview."""
        from .handlers import handle_get_broker_overview

        return handle_get_broker_overview(module._get_admin())

    @mcp.tool()
    def rabbitmq_broker_is_in_alarm() -> Any:
        """DEPRECATED: use health(check='alarms') instead. Check if broker has active alarms."""
        from .handlers import handle_is_broker_in_alarm

        return handle_is_broker_in_alarm(module._get_admin())

    @mcp.tool()
    def rabbitmq_broker_enqueue(queue_name: str, message: str) -> str:
        """DEPRECATED: use publish(method='amqp_queue', target=..., message=...) instead. Publish to queue via AMQP."""
        from .handlers import handle_enqueue

        handle_enqueue(module._get_rmq(), queue_name, message)
        return f"Published to queue {queue_name}"

    @mcp.tool()
    def rabbitmq_broker_delete_queue(name: str, vhost: str = "/") -> str:
        """DEPRECATED: use manage_queue(action='delete', name=..., vhost=...) instead. Delete a queue."""
        from .handlers import handle_delete_queue

        handle_delete_queue(module._get_admin(), name, vhost)
        return f"Queue {name} deleted"

    @mcp.tool()
    def rabbitmq_broker_create_queue(
        name: str,
        vhost: str = "/",
        queue_type: str = "quorum",
        durable: bool = True,
        arguments: dict | None = None,
    ) -> str:
        """DEPRECATED: use manage_queue(action='create', name=...) instead. Create a queue."""
        from .handlers import handle_create_queue
        from .connection import validate_rabbitmq_name

        validate_rabbitmq_name(name, "Queue name")
        handle_create_queue(module._get_admin(), name, vhost, queue_type, durable, False, arguments)
        return f"Queue {name} created ({queue_type})"
