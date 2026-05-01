# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Shared fixtures for integration tests.

Requires a running RabbitMQ broker: docker compose up -d
"""

import pytest

from src.rabbitmq.admin import RabbitMQAdmin
from src.rabbitmq.connection import RabbitMQConnection

HOSTNAME = "localhost"
USERNAME = "guest"
PASSWORD = "guest"

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def admin():
    """RabbitMQAdmin connected to local broker."""
    a = RabbitMQAdmin(HOSTNAME, USERNAME, PASSWORD, use_tls=False)
    try:
        a.test_connection()
    except Exception:
        pytest.skip("RabbitMQ broker not available — run: docker compose up -d")
    return a


@pytest.fixture(scope="module")
def rmq():
    """RabbitMQConnection to local broker."""
    return RabbitMQConnection(HOSTNAME, USERNAME, PASSWORD, port=5672, use_tls=False)
