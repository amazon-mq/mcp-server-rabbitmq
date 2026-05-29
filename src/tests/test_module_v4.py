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

"""Unit tests for src.rabbitmq.module_v4 - mock-based, no live broker needed."""

from unittest.mock import MagicMock, patch

import pytest

from src.rabbitmq.module_v4 import RabbitMQModuleV4, TOOL_GROUPS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance that captures registered tool functions."""
    mcp = MagicMock()
    # Each call to mcp.tool() returns a decorator that stores the function
    registered = {}

    def tool_decorator(**kwargs):
        def decorator(fn):
            registered[fn.__name__] = fn
            return fn
        return decorator

    # Support both @mcp.tool() and @mcp.tool (no parens)
    mcp.tool.side_effect = lambda **kwargs: lambda fn: _register(fn)
    mcp.tool.return_value = lambda fn: _register(fn)

    def _register(fn):
        registered[fn.__name__] = fn
        return fn

    # Override: mcp.tool() called with no args returns a decorator
    def tool_factory(*args, **kwargs):
        if args and callable(args[0]):
            # @mcp.tool without parens
            return _register(args[0])
        # @mcp.tool() with parens
        return _register

    mcp.tool = tool_factory
    mcp._registered = registered
    return mcp


@pytest.fixture
def mock_admin():
    return MagicMock()


@pytest.fixture
def mock_rmq():
    return MagicMock()


@pytest.fixture
def module_with_broker(mock_mcp, mock_admin, mock_rmq):
    """Module with a pre-configured active broker (bypasses connect)."""
    module = RabbitMQModuleV4(mock_mcp)
    module.brokers["test"] = {
        "rmq": mock_rmq,
        "rmq_admin": mock_admin,
        "hostname": "localhost",
    }
    module.active_alias = "test"
    module.register_tools(TOOL_GROUPS)
    return module


@pytest.fixture
def tools(mock_mcp, module_with_broker):
    """Shortcut to access registered tool functions."""
    return mock_mcp._registered


# ---------------------------------------------------------------------------
# Tool Registration Tests
# ---------------------------------------------------------------------------


class TestToolRegistration:
    def test_all_groups_register(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(TOOL_GROUPS)
        # Expect ~28 tools across all groups
        count = len(mock_mcp._registered)
        assert count >= 26, f"Expected ~28 tools, got {count}"
        assert count <= 32, f"Expected ~28 tools, got {count}"

    def test_core_group_loads_independently(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(("core",))
        names = set(mock_mcp._registered.keys())
        assert "connect" in names
        assert "broker" in names
        assert "get_skill" in names
        assert "get_guideline" in names

    def test_read_group_loads_independently(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(("read",))
        names = set(mock_mcp._registered.keys())
        assert "queues" in names
        assert "exchanges" in names
        assert "connections" in names
        assert "overview" in names

    def test_mutative_group_loads_independently(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(("mutative",))
        names = set(mock_mcp._registered.keys())
        assert "manage_queue" in names
        assert "publish" in names
        assert "manage_exchange" in names

    def test_health_group_loads_independently(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(("health",))
        names = set(mock_mcp._registered.keys())
        assert "health" in names

    def test_observability_group_loads_independently(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(("observability",))
        names = set(mock_mcp._registered.keys())
        assert "find_queues" in names

    def test_migration_group_loads_independently(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        module.register_tools(("migration",))
        names = set(mock_mcp._registered.keys())
        assert "definitions_export" in names
        assert "definitions_import" in names
        assert "definitions_compare" in names


# ---------------------------------------------------------------------------
# Queues Dispatcher Tests
# ---------------------------------------------------------------------------


class TestQueuesDispatcher:
    @patch("src.rabbitmq.module_v4.handle_list_queues_by_vhost")
    def test_queues_list(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = [{"name": "q1"}]
        result = tools["queues"](action="list", vhost="/")
        mock_handler.assert_called_once_with(mock_admin, "/")
        assert result == [{"name": "q1"}]

    @patch("src.rabbitmq.module_v4.handle_get_queue_info")
    def test_queues_info(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = {"name": "q1", "messages": 5}
        result = tools["queues"](action="info", name="q1", vhost="/")
        mock_handler.assert_called_once_with(mock_admin, "q1", "/")
        assert result["messages"] == 5

    @patch("src.rabbitmq.module_v4.handle_get_messages")
    def test_queues_messages(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = [{"payload": "hello"}]
        result = tools["queues"](action="messages", name="q1", vhost="/", count=1)
        mock_handler.assert_called_once_with(mock_admin, "q1", "/", 1)

    @patch("src.rabbitmq.module_v4.handle_get_bindings")
    def test_queues_bindings(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = []
        result = tools["queues"](action="bindings", name="q1", vhost="/")
        mock_handler.assert_called_once_with(mock_admin, queue="q1", vhost="/")

    def test_queues_info_missing_name_raises(self, tools):
        with pytest.raises(ValueError, match="name required"):
            tools["queues"](action="info", name=None, vhost="/")

    def test_queues_messages_missing_name_raises(self, tools):
        with pytest.raises(ValueError, match="name required"):
            tools["queues"](action="messages", name=None, vhost="/", count=1)


# ---------------------------------------------------------------------------
# Exchanges Dispatcher Tests
# ---------------------------------------------------------------------------


class TestExchangesDispatcher:
    @patch("src.rabbitmq.module_v4.handle_list_exchanges_by_vhost")
    def test_exchanges_list(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = [{"name": "ex1"}]
        result = tools["exchanges"](action="list", vhost="/")
        mock_handler.assert_called_once_with(mock_admin, "/")

    @patch("src.rabbitmq.module_v4.handle_get_exchange_info")
    def test_exchanges_info(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = {"name": "ex1", "type": "direct"}
        result = tools["exchanges"](action="info", name="ex1", vhost="/")
        mock_handler.assert_called_once_with(mock_admin, "ex1", "/")

    @patch("src.rabbitmq.module_v4.handle_get_bindings")
    def test_exchanges_bindings(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = []
        result = tools["exchanges"](action="bindings", name="ex1", vhost="/")
        mock_handler.assert_called_once_with(mock_admin, exchange="ex1", vhost="/")

    def test_exchanges_info_missing_name_raises(self, tools):
        with pytest.raises(ValueError, match="name required"):
            tools["exchanges"](action="info", name=None, vhost="/")


# ---------------------------------------------------------------------------
# Health Dispatcher Tests
# ---------------------------------------------------------------------------


class TestHealthDispatcher:
    @patch("src.rabbitmq.module_v4.handle_check_local_alarms")
    def test_health_alarms(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = {"status": "ok"}
        result = tools["health"](check="alarms")
        mock_handler.assert_called_once_with(mock_admin)

    @patch("src.rabbitmq.module_v4.handle_is_node_in_quorum_critical")
    def test_health_quorum(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = False
        result = tools["health"](check="quorum")
        mock_handler.assert_called_once_with(mock_admin)

    @patch("src.rabbitmq.module_v4.handle_check_certificate_expiration")
    def test_health_certificates(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = {"expiring_soon": []}
        result = tools["health"](check="certificates", within=30, unit="days")
        mock_handler.assert_called_once_with(mock_admin, 30, "days")

    @patch("src.rabbitmq.module_v4.handle_check_protocol_listener")
    def test_health_protocol(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = True
        result = tools["health"](check="protocol", protocol="amqp")
        mock_handler.assert_called_once_with(mock_admin, "amqp")

    def test_health_protocol_missing_raises(self, tools):
        with pytest.raises(ValueError, match="protocol required"):
            tools["health"](check="protocol", protocol=None, within=30, unit="days")

    @patch("src.rabbitmq.module_v4.handle_check_virtual_hosts")
    def test_health_vhosts(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = {"healthy": True}
        result = tools["health"](check="vhosts")
        mock_handler.assert_called_once_with(mock_admin)

    @patch("src.rabbitmq.module_v4.handle_list_feature_flags")
    def test_health_features(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = []
        result = tools["health"](check="features")
        mock_handler.assert_called_once_with(mock_admin)

    @patch("src.rabbitmq.module_v4.handle_list_deprecated_features")
    def test_health_deprecated(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = []
        result = tools["health"](check="deprecated")
        mock_handler.assert_called_once_with(mock_admin)


# ---------------------------------------------------------------------------
# Manage Queue Dispatcher Tests
# ---------------------------------------------------------------------------


class TestManageQueueDispatcher:
    @patch("src.rabbitmq.module_v4.handle_create_queue")
    @patch("src.rabbitmq.module_v4.validate_rabbitmq_name")
    def test_manage_queue_create(self, mock_validate, mock_handler, tools, mock_admin):
        result = tools["manage_queue"](
            action="create", name="test-q", vhost="/", queue_type="quorum", durable=True, arguments=None
        )
        mock_validate.assert_called_once_with("test-q", "Queue name")
        mock_handler.assert_called_once_with(mock_admin, "test-q", "/", "quorum", True, False, None)
        assert "created" in result

    @patch("src.rabbitmq.module_v4.handle_delete_queue")
    @patch("src.rabbitmq.module_v4.validate_rabbitmq_name")
    def test_manage_queue_delete(self, mock_validate, mock_handler, tools, mock_admin):
        result = tools["manage_queue"](
            action="delete", name="test-q", vhost="/", queue_type="quorum", durable=True, arguments=None
        )
        mock_handler.assert_called_once_with(mock_admin, "test-q", "/")
        assert "deleted" in result

    @patch("src.rabbitmq.module_v4.handle_purge_queue")
    @patch("src.rabbitmq.module_v4.validate_rabbitmq_name")
    def test_manage_queue_purge(self, mock_validate, mock_handler, tools, mock_admin):
        result = tools["manage_queue"](
            action="purge", name="test-q", vhost="/", queue_type="quorum", durable=True, arguments=None
        )
        mock_handler.assert_called_once_with(mock_admin, "test-q", "/")
        assert "purged" in result


# ---------------------------------------------------------------------------
# Publish Dispatcher Tests
# ---------------------------------------------------------------------------


class TestPublishDispatcher:
    @patch("src.rabbitmq.module_v4.handle_enqueue")
    def test_publish_amqp_queue(self, mock_handler, tools, mock_rmq):
        result = tools["publish"](
            method="amqp_queue", target="my-queue", message="hello",
            routing_key="", vhost="/", properties=None
        )
        mock_handler.assert_called_once_with(mock_rmq, "my-queue", "hello")
        assert "queue" in result.lower()

    @patch("src.rabbitmq.module_v4.handle_fanout")
    def test_publish_amqp_fanout(self, mock_handler, tools, mock_rmq):
        result = tools["publish"](
            method="amqp_fanout", target="my-exchange", message="hello",
            routing_key="", vhost="/", properties=None
        )
        mock_handler.assert_called_once_with(mock_rmq, "my-exchange", "hello")
        assert "fanout" in result.lower()

    @patch("src.rabbitmq.module_v4.handle_publish_message")
    def test_publish_http(self, mock_handler, tools, mock_admin):
        mock_handler.return_value = {"routed": True}
        result = tools["publish"](
            method="http", target="my-exchange", message="hello",
            routing_key="rk", vhost="/", properties={"content_type": "text/plain"}
        )
        mock_handler.assert_called_once_with(
            mock_admin, "my-exchange", "rk", "hello", "/", {"content_type": "text/plain"}
        )
        assert "http" in result.lower()


# ---------------------------------------------------------------------------
# Error Cases
# ---------------------------------------------------------------------------


class TestErrorCases:
    def test_get_admin_no_broker_raises(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        with pytest.raises(AssertionError, match="No active broker"):
            module._get_admin()

    def test_get_rmq_no_broker_raises(self, mock_mcp):
        module = RabbitMQModuleV4(mock_mcp)
        with pytest.raises(AssertionError, match="No active broker"):
            module._get_rmq()

    def test_manage_policy_create_missing_definition_raises(self, tools):
        with pytest.raises(ValueError, match="definition required"):
            tools["manage_policy"](
                action="create", name="p1", pattern=".*",
                definition=None, vhost="/", priority=0, apply_to="all"
            )

    def test_manage_binding_delete_missing_props_key_raises(self, tools):
        with pytest.raises(ValueError, match="props_key required"):
            tools["manage_binding"](
                action="delete", exchange="ex", queue="q",
                routing_key="", vhost="/", props_key=None, arguments=None
            )

    def test_cluster_node_info_missing_name_raises(self, tools):
        with pytest.raises(ValueError, match="node_name required"):
            tools["cluster"](action="node_info", node_name=None)

    def test_cluster_node_memory_missing_name_raises(self, tools):
        with pytest.raises(ValueError, match="node_name required"):
            tools["cluster"](action="node_memory", node_name=None)
