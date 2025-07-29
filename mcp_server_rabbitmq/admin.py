import base64
from typing import Dict, List, Optional

import requests

from mcp_server_rabbitmq.connection import validate_rabbitmq_name


class RabbitMQAdmin:
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool):
        self.protocol = "https" if use_tls else "http"
        self.base_url = f"{self.protocol}://{host}:{port}/api"
        self.auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {self.auth}", "Content-Type": "application/json"}

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> requests.Response:
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data, verify=True)
        response.raise_for_status()
        return response

    def list_queues(self) -> List[Dict]:
        """List all queues in the RabbitMQ server"""
        response = self._make_request("GET", "queues")
        return response.json()

    def list_queues_by_vhost(self, vhost: str = "/") -> List[Dict]:
        """List all queues in the RabbitMQ server for a specific vhost"""
        vhost_encoded = requests.utils.quote(vhost, safe="")
        response = self._make_request("GET", f"queues/{vhost_encoded}")
        return response.json()

    def list_exchanges(self) -> List[Dict]:
        """List all exchanges in the RabbitMQ server"""
        response = self._make_request("GET", "exchanges")
        return response.json()

    def list_exchanges_by_vhost(self, vhost: str = "/") -> List[Dict]:
        """List all exchanges in the RabbitMQ server for a specific vhost"""
        vhost_encoded = requests.utils.quote(vhost, safe="")
        response = self._make_request("GET", f"exchanges/{vhost_encoded}")
        return response.json()

    def get_queue_info(self, queue: str, vhost: str = "/") -> Dict:
        """Get detailed information about a specific queue"""
        vhost_encoded = requests.utils.quote(vhost, safe="")
        response = self._make_request("GET", f"queues/{vhost_encoded}/{queue}")
        return response.json()

    def delete_queue(self, queue: str, vhost: str = "/") -> None:
        """Delete a queue"""
        validate_rabbitmq_name(queue, "Queue name")
        vhost_encoded = requests.utils.quote(vhost, safe="")
        self._make_request("DELETE", f"queues/{vhost_encoded}/{queue}")

    def purge_queue(self, queue: str, vhost: str = "/") -> None:
        """Remove all messages from a queue"""
        validate_rabbitmq_name(queue, "Queue name")
        vhost_encoded = requests.utils.quote(vhost, safe="")
        self._make_request("DELETE", f"queues/{vhost_encoded}/{queue}/contents")

    def get_exchange_info(self, exchange: str, vhost: str = "/") -> Dict:
        """Get detailed information about a specific exchange"""
        vhost_encoded = requests.utils.quote(vhost, safe="")
        response = self._make_request("GET", f"exchanges/{vhost_encoded}/{exchange}")
        return response.json()

    def delete_exchange(self, exchange: str, vhost: str = "/") -> None:
        """Delete an exchange"""
        validate_rabbitmq_name(exchange, "Exchange name")
        vhost_encoded = requests.utils.quote(vhost, safe="")
        self._make_request("DELETE", f"exchanges/{vhost_encoded}/{exchange}")

    def get_bindings(
        self, queue: Optional[str] = None, exchange: Optional[str] = None, vhost: str = "/"
    ) -> List[Dict]:
        """Get bindings, optionally filtered by queue or exchange"""
        vhost_encoded = requests.utils.quote(vhost, safe="")
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

    def get_overview(self) -> Dict:
        """Get overview of RabbitMQ server including version, stats, and listeners"""
        response = self._make_request("GET", "overview")
        return response.json()

    def list_vhosts(self) -> Dict:
        """List all vhost in the RabbitMQ server"""
        response = self._make_request("GET", "vhosts")
        return response.json()

    def list_shovels(self) -> List[Dict]:
        """List all shovels in the RabbitMQ server"""
        response = self._make_request("GET", "shovels")
        return response.json()

    def get_shovel_info(self, shovel_name: str, vhost: str = "/") -> Dict:
        """Get detailed information about a specific shovel in a vhost"""
        vhost_encoded = requests.utils.quote(vhost, safe="")
        response = self._make_request("GET", f"parameters/shovel/{vhost_encoded}/{shovel_name}")
        return response.json()
