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

"""Optional broker configuration from the environment.

Some MCP hosts (aggregators and proxies) start a fresh server process per
session, or even per tool call. State established by the connect tool does not
survive that, so every subsequent tool fails with "No active broker".

Setting one or both endpoint URIs lets the server connect during startup
instead, so the tools are usable on every spawn without a connect call:

    RABBITMQ_AMQP_ENDPOINT=amqps://user:pass@broker.example.com:5671
    RABBITMQ_MANAGEMENT_ENDPOINT=https://user:pass@broker.example.com:443

Either variable is sufficient on its own; the other is derived from it. The
scheme carries TLS, so there is no separate flag that can contradict the port.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import unquote, urlsplit

from loguru import logger

from .admin import RabbitMQAdmin
from .connection import RabbitMQConnection

AMQP_ENDPOINT_ENV = "RABBITMQ_AMQP_ENDPOINT"
MANAGEMENT_ENDPOINT_ENV = "RABBITMQ_MANAGEMENT_ENDPOINT"
ALIAS_ENV = "RABBITMQ_ALIAS"

# scheme -> (use_tls, default port)
_SCHEMES: dict[str, tuple[bool, int]] = {
    "amqp": (False, 5672),
    "amqps": (True, 5671),
    "http": (False, 15672),
    "https": (True, 443),
}
_AMQP_SCHEMES = ("amqps", "amqp")
_MANAGEMENT_SCHEMES = ("https", "http")


class BrokerRegistry(Protocol):
    """The broker-registry surface shared by RabbitMQModule and RabbitMQModuleV4."""

    brokers: dict[str, dict]
    active_alias: str | None
    default_management_port: int | None


@dataclass(frozen=True)
class Endpoint:
    """A parsed endpoint URI. Never log this directly; it holds a password."""

    scheme: str
    hostname: str
    username: str
    password: str
    port: int
    use_tls: bool

    @property
    def safe_display(self) -> str:
        """Credential-free rendering, safe for logs and error messages."""
        return f"{self.scheme}://{self.hostname}:{self.port}"


def parse_endpoint(uri: str, allowed_schemes: tuple[str, ...], var_name: str) -> Endpoint:
    """Parse an endpoint URI into connection parameters.

    The port defaults from the scheme when omitted (amqps 5671, amqp 5672,
    https 443, http 15672). Userinfo is percent-decoded, so a password
    containing reserved characters works when encoded, e.g. "p%40ss" -> "p@ss".

    Raises ValueError with a message that never contains the password.
    """
    parts = urlsplit(uri.strip())

    if parts.scheme not in allowed_schemes:
        expected = " or ".join(f"{s}://" for s in allowed_schemes)
        raise ValueError(f"{var_name} must start with {expected}, got '{parts.scheme}://'")

    try:
        port = parts.port
    except ValueError as exc:
        # urlsplit defers port validation to attribute access.
        raise ValueError(f"{var_name} has a non-numeric port") from exc

    if not parts.hostname:
        raise ValueError(f"{var_name} is missing a hostname")
    if not parts.username or parts.password is None:
        raise ValueError(
            f"{var_name} must include credentials, "
            f"e.g. {allowed_schemes[0]}://user:pass@{parts.hostname}"
        )

    use_tls, default_port = _SCHEMES[parts.scheme]
    return Endpoint(
        scheme=parts.scheme,
        hostname=parts.hostname,
        username=unquote(parts.username),
        password=unquote(parts.password),
        port=port or default_port,
        use_tls=use_tls,
    )


def _derive_management(amqp: Endpoint, default_management_port: int | None) -> Endpoint:
    """Build a management endpoint from an AMQP one, reusing host and credentials."""
    scheme = "https" if amqp.use_tls else "http"
    return Endpoint(
        scheme=scheme,
        hostname=amqp.hostname,
        username=amqp.username,
        password=amqp.password,
        port=default_management_port or _SCHEMES[scheme][1],
        use_tls=amqp.use_tls,
    )


def _derive_amqp(management: Endpoint) -> Endpoint:
    """Build an AMQP endpoint from a management one, reusing host and credentials."""
    scheme = "amqps" if management.use_tls else "amqp"
    return Endpoint(
        scheme=scheme,
        hostname=management.hostname,
        username=management.username,
        password=management.password,
        port=_SCHEMES[scheme][1],
        use_tls=management.use_tls,
    )


def auto_connect_from_env(module: BrokerRegistry, env: Mapping[str, str] | None = None) -> bool:
    """Register a broker from the environment, if configured.

    Returns True when a broker was registered and made active. Returns False
    when no endpoint variable is set, or when the configuration is unusable.

    A bad endpoint is logged and skipped rather than raised: aborting startup
    would leave the host with a dead server, whereas continuing leaves the
    connect tool available as it was before.

    Note: env-supplied hostnames are deliberately not passed through
    validate_hostname. That guard exists to stop a model-supplied tool
    argument from reaching loopback or the cloud metadata endpoint. These
    values come from the operator's own process environment, and a local
    broker is the common development case.
    """
    env = os.environ if env is None else env
    amqp_uri = (env.get(AMQP_ENDPOINT_ENV) or "").strip()
    management_uri = (env.get(MANAGEMENT_ENDPOINT_ENV) or "").strip()

    if not amqp_uri and not management_uri:
        return False

    try:
        amqp = parse_endpoint(amqp_uri, _AMQP_SCHEMES, AMQP_ENDPOINT_ENV) if amqp_uri else None
        management = (
            parse_endpoint(management_uri, _MANAGEMENT_SCHEMES, MANAGEMENT_ENDPOINT_ENV)
            if management_uri
            else None
        )
    except ValueError as exc:
        logger.warning(f"Ignoring broker configuration from the environment: {exc}")
        return False

    if amqp is None:
        if management is None:  # unreachable, both-empty returned above
            return False
        amqp = _derive_amqp(management)
    if management is None:
        management = _derive_management(amqp, module.default_management_port)

    alias = (env.get(ALIAS_ENV) or "").strip() or amqp.hostname

    try:
        rmq = RabbitMQConnection(
            hostname=amqp.hostname,
            username=amqp.username,
            password=amqp.password,
            port=amqp.port,
            use_tls=amqp.use_tls,
        )
        rmq_admin = RabbitMQAdmin(
            hostname=management.hostname,
            username=management.username,
            password=management.password,
            use_tls=management.use_tls,
            port=management.port,
        )
        rmq_admin.test_connection()
    except Exception as exc:
        logger.warning(
            f"Could not connect to {management.safe_display} using {AMQP_ENDPOINT_ENV}/"
            f"{MANAGEMENT_ENDPOINT_ENV}: {type(exc).__name__}: {exc}. "
            "The connect tool is still available."
        )
        return False

    module.brokers[alias] = {
        "rmq": rmq,
        "rmq_admin": rmq_admin,
        "hostname": amqp.hostname,
    }
    module.active_alias = alias
    logger.info(f"Connected to {amqp.safe_display} as '{alias}' from the environment")
    return True
