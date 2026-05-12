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

import base64
from typing import Any, Optional
from urllib.parse import quote

import requests

from .connection import validate_rabbitmq_name

REQUEST_TIMEOUT = (5, 30)


# https://rawcdn.githack.com/rabbitmq/rabbitmq-server/v4.0.7/deps/rabbitmq_management/priv/www/api/index.html
class RabbitMQAdmin:
    """RabbitMQAdmin class provides API to call RabbitMQ APIs."""

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        use_tls: bool = True,
        port: int | None = None,
    ):
        """Initialize RabbitMQ admin client."""
        self.protocol = "https" if use_tls else "http"
        if port is None:
            port = 443 if use_tls else 15672
        self.base_url = f"{self.protocol}://{hostname}:{port}/api"
        self._username = username
        self._password = password

    @property
    def headers(self) -> dict:
        """Generate auth headers on demand to avoid storing encoded credentials."""
        auth = base64.b64encode(f"{self._username}:{self._password}".encode()).decode()
        return {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

    def _make_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> requests.Response:
        """Make HTTP request to RabbitMQ API."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(
            method, url, headers=self.headers, json=data, verify=True, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response

    def test_connection(self):
        """Test if the RabbitMQ admin HTTP endpoints are accessible."""
        self._make_request("GET", "queues")

    def list_queues(self) -> list[dict]:
        """List all queues in the RabbitMQ server."""
        response = self._make_request("GET", "queues")
        return response.json()

    def list_queues_by_vhost(self, vhost: str = "/") -> list[dict]:
        """List all queues in the RabbitMQ server for a specific vhost."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"queues/{vhost_encoded}")
        return response.json()

    def list_queues_with_details(self, vhost: str = "/") -> list[dict]:
        """List all queues in a vhost with full detail (for threshold filtering)."""
        return self.list_queues_by_vhost(vhost)

    def list_exchanges(self) -> list[dict]:
        """List all exchanges in the RabbitMQ server."""
        response = self._make_request("GET", "exchanges")
        return response.json()

    def list_exchanges_by_vhost(self, vhost: str = "/") -> list[dict]:
        """List all exchanges in the RabbitMQ server for a specific vhost."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"exchanges/{vhost_encoded}")
        return response.json()

    def get_queue_info(self, queue: str, vhost: str = "/") -> dict:
        """Get detailed information about a specific queue."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"queues/{vhost_encoded}/{queue}")
        return response.json()

    def delete_queue(self, queue: str, vhost: str = "/") -> None:
        """Delete a queue."""
        validate_rabbitmq_name(queue, "Queue name")
        vhost_encoded = quote(vhost, safe="")
        self._make_request("DELETE", f"queues/{vhost_encoded}/{queue}")

    def purge_queue(self, queue: str, vhost: str = "/") -> None:
        """Remove all messages from a queue."""
        validate_rabbitmq_name(queue, "Queue name")
        vhost_encoded = quote(vhost, safe="")
        self._make_request("DELETE", f"queues/{vhost_encoded}/{queue}/contents")

    def get_exchange_info(self, exchange: str, vhost: str = "/") -> dict:
        """Get detailed information about a specific exchange."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"exchanges/{vhost_encoded}/{exchange}")
        return response.json()

    def delete_exchange(self, exchange: str, vhost: str = "/") -> None:
        """Delete an exchange."""
        validate_rabbitmq_name(exchange, "Exchange name")
        vhost_encoded = quote(vhost, safe="")
        self._make_request("DELETE", f"exchanges/{vhost_encoded}/{exchange}")

    def get_bindings(
        self, queue: Optional[str] = None, exchange: Optional[str] = None, vhost: str = "/"
    ) -> list[dict]:
        """Get bindings, optionally filtered by queue or exchange."""
        vhost_encoded = quote(vhost, safe="")
        if queue:
            validate_rabbitmq_name(queue, "Queue name")
            response = self._make_request("GET", f"queues/{vhost_encoded}/{queue}/bindings")
        elif exchange:
            validate_rabbitmq_name(exchange, "Exchange name")
            response = self._make_request(
                "GET", f"exchanges/{vhost_encoded}/{exchange}/bindings/source"
            )
        else:
            response = self._make_request("GET", f"bindings/{vhost_encoded}")
        return response.json()

    def get_overview(self) -> dict:
        """Get overview of RabbitMQ server including version, stats, and listeners."""
        response = self._make_request("GET", "overview")
        return response.json()

    def list_vhosts(self) -> dict:
        """List all vhost in the RabbitMQ server."""
        response = self._make_request("GET", "vhosts")
        return response.json()

    def list_shovels(self) -> list[dict]:
        """List all shovels in the RabbitMQ server."""
        response = self._make_request("GET", "shovels")
        return response.json()

    def get_shovel_info(self, shovel_name: str, vhost: str = "/") -> dict:
        """Get detailed information about a specific shovel in a vhost."""
        vhost_encoded = quote(vhost, safe="")
        shovel_encoded = quote(shovel_name, safe="")
        response = self._make_request("GET", f"parameters/shovel/{vhost_encoded}/{shovel_encoded}")
        return response.json()

    def get_cluster_nodes(self) -> dict:
        """Get a list of nodes in the RabbitMQ cluster."""
        response = self._make_request("GET", "nodes")
        return response.json()

    def get_node_information(self, node_name: str) -> dict:
        """Get a node information."""
        node_encoded = quote(node_name, safe="")
        response = self._make_request("GET", f"nodes/{node_encoded}")
        return response.json()

    def get_node_memory(self, node_name: str) -> dict:
        """Get a node memory usage breakdown information."""
        node_encoded = quote(node_name, safe="")
        response = self._make_request("GET", f"nodes/{node_encoded}/memory")
        return response.json()

    def list_connections(self) -> dict:
        """List all connections on the RabbitMQ broker."""
        response = self._make_request("GET", "connections")
        return response.json()

    def list_consumers(self) -> Any:
        """List all consumers on the RabbitMQ broker."""
        response = self._make_request("GET", "consumers")
        return response.json()

    def list_users(self) -> Any:
        """List all users on the RabbitMQ broker."""
        response = self._make_request("GET", "users")
        return response.json()

    def get_alarm_status(self) -> int:
        """Get the alarm status of the RabbitMQ broker."""
        response = self._make_request("GET", "health/checks/alarms")
        return response.status_code

    def get_is_node_quorum_critical(self) -> int:
        """Check if there are quorum queues with minimum online quorum."""
        response = self._make_request("GET", "checks/node-is-quorum-critical")
        return response.status_code

    def get_broker_definition(self) -> dict:
        """Get the broker definition."""
        response = self._make_request("GET", "definitions")
        return response.json()

    def update_broker_definition(self, definition: dict) -> None:
        """Upload broker definitions (exchanges, queues, bindings, policies)."""
        self._make_request("POST", "definitions", data=definition)

    def create_queue(self, queue: str, vhost: str = "/", **kwargs) -> None:
        """Create a queue."""
        validate_rabbitmq_name(queue, "Queue name")
        vhost_encoded = quote(vhost, safe="")
        self._make_request("PUT", f"queues/{vhost_encoded}/{queue}", data=kwargs or {})

    def create_exchange(
        self, exchange: str, exchange_type: str = "direct", vhost: str = "/", **kwargs
    ) -> None:
        """Create an exchange."""
        validate_rabbitmq_name(exchange, "Exchange name")
        vhost_encoded = quote(vhost, safe="")
        data = {"type": exchange_type, **kwargs}
        self._make_request("PUT", f"exchanges/{vhost_encoded}/{exchange}", data=data)

    def create_binding(
        self,
        vhost: str,
        exchange: str,
        queue: str,
        routing_key: str = "",
        arguments: dict | None = None,
    ) -> None:
        """Create a binding from exchange to queue."""
        vhost_encoded = quote(vhost, safe="")
        data: dict = {"routing_key": routing_key}
        if arguments:
            data["arguments"] = arguments
        self._make_request("POST", f"bindings/{vhost_encoded}/e/{exchange}/q/{queue}", data=data)

    def delete_binding(self, vhost: str, exchange: str, queue: str, props_key: str) -> None:
        """Delete a binding."""
        vhost_encoded = quote(vhost, safe="")
        self._make_request(
            "DELETE", f"bindings/{vhost_encoded}/e/{exchange}/q/{queue}/{props_key}"
        )

    def list_policies(self, vhost: str = "/") -> list[dict]:
        """List all policies in a vhost."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"policies/{vhost_encoded}")
        return response.json()

    def get_policy(self, name: str, vhost: str = "/") -> dict:
        """Get a specific policy."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"policies/{vhost_encoded}/{name}")
        return response.json()

    def create_policy(
        self,
        name: str,
        pattern: str,
        definition: dict,
        vhost: str = "/",
        priority: int = 0,
        apply_to: str = "all",
    ) -> None:
        """Create or update a policy."""
        vhost_encoded = quote(vhost, safe="")
        data = {
            "pattern": pattern,
            "definition": definition,
            "priority": priority,
            "apply-to": apply_to,
        }
        self._make_request("PUT", f"policies/{vhost_encoded}/{name}", data=data)

    def delete_policy(self, name: str, vhost: str = "/") -> None:
        """Delete a policy."""
        vhost_encoded = quote(vhost, safe="")
        self._make_request("DELETE", f"policies/{vhost_encoded}/{name}")

    def publish_message(
        self,
        exchange: str,
        routing_key: str,
        payload: str,
        vhost: str = "/",
        properties: dict | None = None,
    ) -> dict:
        """Publish a message via the HTTP API."""
        vhost_encoded = quote(vhost, safe="")
        data = {
            "routing_key": routing_key,
            "payload": payload,
            "payload_encoding": "string",
            "properties": properties or {},
        }
        response = self._make_request(
            "POST", f"exchanges/{vhost_encoded}/{exchange}/publish", data=data
        )
        return response.json()

    def get_messages(
        self,
        queue: str,
        vhost: str = "/",
        count: int = 1,
        ackmode: str = "ack_requeue_true",
        encoding: str = "auto",
    ) -> list[dict]:
        """Get messages from a queue (peek)."""
        vhost_encoded = quote(vhost, safe="")
        data = {"count": count, "ackmode": ackmode, "encoding": encoding}
        response = self._make_request("POST", f"queues/{vhost_encoded}/{queue}/get", data=data)
        return response.json()

    def list_channels(self) -> list[dict]:
        """List all open channels."""
        response = self._make_request("GET", "channels")
        return response.json()

    def close_connection(self, name: str) -> None:
        """Close a connection."""
        name_encoded = quote(name, safe="")
        self._make_request("DELETE", f"connections/{name_encoded}")

    def create_vhost(self, name: str) -> None:
        """Create a virtual host."""
        name_encoded = quote(name, safe="")
        self._make_request("PUT", f"vhosts/{name_encoded}", data={})

    def delete_vhost(self, name: str) -> None:
        """Delete a virtual host."""
        name_encoded = quote(name, safe="")
        self._make_request("DELETE", f"vhosts/{name_encoded}")

    def get_permissions(self, vhost: str, user: str) -> dict:
        """Get permissions for a user in a vhost."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"permissions/{vhost_encoded}/{user}")
        return response.json()

    def set_permissions(
        self, vhost: str, user: str, configure: str = ".*", write: str = ".*", read: str = ".*"
    ) -> None:
        """Set permissions for a user in a vhost."""
        vhost_encoded = quote(vhost, safe="")
        data = {"configure": configure, "write": write, "read": read}
        self._make_request("PUT", f"permissions/{vhost_encoded}/{user}", data=data)

    # --- Federation ---

    def list_federation_upstreams(self, vhost: str = "/") -> list[dict]:
        """List federation upstreams in a vhost."""
        vhost_encoded = quote(vhost, safe="")
        response = self._make_request("GET", f"parameters/federation-upstream/{vhost_encoded}")
        return response.json()

    def create_federation_upstream(self, name: str, uri: str, vhost: str = "/", **kwargs) -> None:
        """Create a federation upstream."""
        vhost_encoded = quote(vhost, safe="")
        value = {"uri": uri, **kwargs}
        data = {"value": value}
        self._make_request(
            "PUT", f"parameters/federation-upstream/{vhost_encoded}/{name}", data=data
        )

    def delete_federation_upstream(self, name: str, vhost: str = "/") -> None:
        """Delete a federation upstream."""
        vhost_encoded = quote(vhost, safe="")
        self._make_request("DELETE", f"parameters/federation-upstream/{vhost_encoded}/{name}")

    # --- Health & Ops ---

    def _health_check(self, endpoint: str) -> dict:
        """Make a health check request that doesn't raise on non-2xx status."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(
                url, headers=self.headers, verify=True, timeout=REQUEST_TIMEOUT
            )
            return {"status": response.status_code, "ok": response.status_code == 200}
        except requests.RequestException as e:
            return {"status": 0, "ok": False, "error": str(e)}

    def check_local_alarms(self) -> dict:
        """Check for local alarms."""
        return self._health_check("health/checks/local-alarms")

    def check_certificate_expiration(self, within: int = 30, unit: str = "days") -> dict:
        """Check if any certificates expire within the given timeframe."""
        return self._health_check(f"health/checks/certificate-expiration/{within}/{unit}")

    def check_protocol_listener(self, protocol: str) -> dict:
        """Check if a protocol listener is active."""
        protocol_encoded = quote(protocol, safe="")
        return self._health_check(f"health/checks/protocol-listener/{protocol_encoded}")

    def check_virtual_hosts(self) -> dict:
        """Check health of all virtual hosts."""
        return self._health_check("health/checks/virtual-hosts")

    def list_feature_flags(self) -> list[dict]:
        """List all feature flags."""
        response = self._make_request("GET", "feature-flags")
        return response.json()

    def list_deprecated_features_in_use(self) -> list[dict]:
        """List deprecated features currently in use."""
        response = self._make_request("GET", "deprecated-features/used")
        return response.json()

    def rebalance_queues(self) -> None:
        """Rebalance queue leaders across cluster nodes."""
        self._make_request("POST", "rebalance/queues", data={})

    def whoami(self) -> dict:
        """Get the current authenticated user."""
        response = self._make_request("GET", "whoami")
        return response.json()
