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

import ipaddress
import ssl
from typing import Any

import pika
from loguru import logger


class RabbitMQConnection:
    """RabbitMQ connection manager for message operations."""

    def __init__(
        self, hostname: str, username: str, password: str, port: int = 5671, use_tls: bool = True
    ):
        """Initialize RabbitMQ connection parameters."""
        if not use_tls:
            logger.warning("Connecting to broker without TLS - credentials will be sent in plaintext")
        credentials = pika.PlainCredentials(username, password)
        ssl_options = None
        if use_tls:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_options = pika.SSLOptions(context=ssl_context)
        self.parameters = pika.ConnectionParameters(
            host=hostname,
            port=port,
            credentials=credentials,
            ssl_options=ssl_options,
        )

    def get_channel(self) -> tuple[Any, Any]:
        """Create and return a connection and channel for RabbitMQ operations."""
        connection = pika.BlockingConnection(self.parameters)
        channel = connection.channel()
        return connection, channel


def validate_rabbitmq_name(name: str, field_name: str) -> None:
    """Validate RabbitMQ queue/exchange names."""
    if not name or not name.strip():
        raise ValueError(f"{field_name} cannot be empty")
    if not all(c.isalnum() or c in "-_.:" for c in name):
        raise ValueError(
            f"{field_name} can only contain letters, digits, hyphen, underscore, period, or colon"
        )
    if len(name) > 255:
        raise ValueError(f"{field_name} must be less than 255 characters")


def validate_hostname(hostname: str) -> None:
    """Validate hostname to block SSRF against internal/loopback addresses.

    If the hostname is a DNS name (not an IP literal), it is allowed through
    since we cannot resolve it without an allowlist.
    """
    if not hostname or not hostname.strip():
        raise ValueError("Hostname cannot be empty")

    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        # Not an IP literal (it is a DNS name) - allow it
        return

    # IPv4 loopback: 127.0.0.0/8
    if addr.is_loopback:
        raise ValueError(f"Hostname {hostname} is a loopback address and is not allowed")

    # IPv6 loopback: ::1
    if addr == ipaddress.ip_address("::1"):
        raise ValueError(f"Hostname {hostname} is a loopback address and is not allowed")

    # IPv4 link-local metadata endpoint: 169.254.169.254
    if addr == ipaddress.ip_address("169.254.169.254"):
        raise ValueError(
            f"Hostname {hostname} is the cloud metadata endpoint and is not allowed"
        )

    # IPv4 link-local: 169.254.0.0/16
    if addr.is_link_local:
        raise ValueError(f"Hostname {hostname} is a link-local address and is not allowed")
