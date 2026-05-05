# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for RabbitMQ admin operations.

Run: docker compose up -d && pytest src/tests/integration/ -v

Tests within each class run in definition order (pytest default) and are
intentionally sequential: create → operate → delete.
"""

from src.rabbitmq.handlers import (
    handle_check_local_alarms,
    handle_check_virtual_hosts,
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
    handle_export_definitions,
    handle_get_bindings,
    handle_get_cluster_nodes,
    handle_get_definition,
    handle_get_exchange_info,
    handle_get_messages,
    handle_get_node_information,
    handle_get_permissions,
    handle_get_queue_info,
    handle_is_broker_in_alarm,
    handle_is_node_in_quorum_critical,
    handle_list_channels,
    handle_list_connections,
    handle_list_consumers,
    handle_list_deprecated_features,
    handle_list_exchanges,
    handle_list_feature_flags,
    handle_list_queues,
    handle_list_shovels,
    handle_list_users,
    handle_list_vhosts,
    handle_publish_message,
    handle_purge_queue,
    handle_set_permissions,
    handle_whoami,
)
from src.rabbitmq.transforms import apply_transforms

TEST_QUEUE = "integration-test-queue"
TEST_EXCHANGE = "integration-test-exchange"
TEST_VHOST = "integration-test-vhost"
TEST_POLICY = "integration-test-policy"


# --- Health & Overview ---


class TestHealth:
    def test_whoami(self, admin):
        result = handle_whoami(admin)
        assert result["name"] == "guest"

    def test_not_in_alarm(self, admin):
        assert handle_is_broker_in_alarm(admin) is False

    def test_not_quorum_critical(self, admin):
        assert handle_is_node_in_quorum_critical(admin) is False

    def test_check_local_alarms(self, admin):
        result = handle_check_local_alarms(admin)
        assert result["ok"] is True

    def test_check_virtual_hosts(self, admin):
        result = handle_check_virtual_hosts(admin)
        assert result["ok"] is True

    def test_list_feature_flags(self, admin):
        result = handle_list_feature_flags(admin)
        assert isinstance(result, list)

    def test_list_deprecated_features(self, admin):
        result = handle_list_deprecated_features(admin)
        assert isinstance(result, list)


# --- Cluster ---


class TestCluster:
    def test_get_cluster_nodes(self, admin):
        result = handle_get_cluster_nodes(admin)
        assert len(result) >= 1
        assert result[0]["running"] is True

    def test_get_node_information(self, admin):
        nodes = admin.get_cluster_nodes()
        node_name = nodes[0]["name"]
        result = handle_get_node_information(admin, node_name)
        assert result["name"] == node_name


# --- Queues ---


class TestQueues:
    """Tests run in definition order: create → list → get → publish → purge → delete."""

    def test_create_queue(self, admin):
        handle_create_queue(admin, TEST_QUEUE, queue_type="classic")

    def test_list_queues(self, admin):
        result = handle_list_queues(admin)
        assert TEST_QUEUE in result

    def test_get_queue_info(self, admin):
        result = handle_get_queue_info(admin, TEST_QUEUE)
        assert result["name"] == TEST_QUEUE

    def test_publish_and_peek(self, admin):
        handle_publish_message(admin, "", TEST_QUEUE, "test-payload")
        messages = handle_get_messages(admin, TEST_QUEUE, count=1)
        assert len(messages) >= 1
        assert messages[0]["payload"] == "test-payload"

    def test_purge_queue(self, admin):
        handle_purge_queue(admin, TEST_QUEUE)
        messages = handle_get_messages(admin, TEST_QUEUE, count=1)
        assert len(messages) == 0

    def test_delete_queue(self, admin):
        handle_delete_queue(admin, TEST_QUEUE)
        result = handle_list_queues(admin)
        assert TEST_QUEUE not in result


# --- Exchanges ---


class TestExchanges:
    """Tests run in definition order: create → list → get → delete."""

    def test_create_exchange(self, admin):
        handle_create_exchange(admin, TEST_EXCHANGE, exchange_type="direct")

    def test_list_exchanges(self, admin):
        result = handle_list_exchanges(admin)
        assert TEST_EXCHANGE in result

    def test_get_exchange_info(self, admin):
        result = handle_get_exchange_info(admin, TEST_EXCHANGE)
        assert result["name"] == TEST_EXCHANGE
        assert result["type"] == "direct"

    def test_delete_exchange(self, admin):
        handle_delete_exchange(admin, TEST_EXCHANGE)
        result = handle_list_exchanges(admin)
        assert TEST_EXCHANGE not in result


# --- Bindings ---


class TestBindings:
    def test_create_and_list_binding(self, admin):
        handle_create_exchange(admin, TEST_EXCHANGE, exchange_type="direct")
        handle_create_queue(admin, TEST_QUEUE, queue_type="classic")
        handle_create_binding(admin, TEST_EXCHANGE, TEST_QUEUE, routing_key="test-key")
        bindings = handle_get_bindings(admin, queue=TEST_QUEUE)
        routing_keys = [b.get("routing_key") for b in bindings]
        assert "test-key" in routing_keys

    def test_delete_binding(self, admin):
        bindings = handle_get_bindings(admin, queue=TEST_QUEUE)
        for b in bindings:
            if b.get("routing_key") == "test-key":
                handle_delete_binding(admin, TEST_EXCHANGE, TEST_QUEUE, b["properties_key"])
        # Cleanup
        handle_delete_queue(admin, TEST_QUEUE)
        handle_delete_exchange(admin, TEST_EXCHANGE)


# --- Policies ---


class TestPolicies:
    """Tests run in definition order: create → list → get → delete."""

    def test_create_policy(self, admin):
        handle_create_policy(admin, TEST_POLICY, ".*", {"max-length": 1000})

    def test_list_policies(self, admin):
        result = admin.list_policies()
        names = [p["name"] for p in result]
        assert TEST_POLICY in names

    def test_get_policy(self, admin):
        result = admin.get_policy(TEST_POLICY)
        assert result["definition"]["max-length"] == 1000

    def test_delete_policy(self, admin):
        handle_delete_policy(admin, TEST_POLICY)


# --- Vhosts & Permissions ---


class TestVhosts:
    """Tests run in definition order: create → permissions → delete."""

    def test_create_vhost(self, admin):
        handle_create_vhost(admin, TEST_VHOST)
        result = handle_list_vhosts(admin)
        assert TEST_VHOST in result

    def test_set_and_get_permissions(self, admin):
        handle_set_permissions(admin, TEST_VHOST, "guest")
        result = handle_get_permissions(admin, TEST_VHOST, "guest")
        assert result["configure"] == ".*"

    def test_delete_vhost(self, admin):
        handle_delete_vhost(admin, TEST_VHOST)
        result = handle_list_vhosts(admin)
        assert TEST_VHOST not in result


# --- Connections, Consumers, Channels ---


class TestConnections:
    def test_list_connections(self, admin):
        result = handle_list_connections(admin)
        assert isinstance(result, list)

    def test_list_consumers(self, admin):
        result = handle_list_consumers(admin)
        assert isinstance(result, list)

    def test_list_channels(self, admin):
        result = handle_list_channels(admin)
        assert isinstance(result, list)

    def test_list_users(self, admin):
        result = handle_list_users(admin)
        names = [u["name"] for u in result]
        assert "guest" in names

    def test_list_shovels(self, admin):
        result = handle_list_shovels(admin)
        assert isinstance(result, list)


# --- Definitions & Transforms ---


class TestDefinitions:
    def test_get_definition(self, admin):
        result = handle_get_definition(admin)
        assert "queues" in result
        assert "exchanges" in result

    def test_export_with_transforms(self, admin):
        result = handle_export_definitions(admin, ["exclude_users", "exclude_permissions"])
        assert "users" not in result
        assert "permissions" not in result

    def test_compare_identical(self, admin):
        defs = admin.get_broker_definition()
        result = handle_compare_definitions(defs, defs)
        assert result == {"status": "identical"}

    def test_transforms_strip_cmq(self):
        defs = {
            "policies": [
                {"name": "ha", "definition": {"ha-mode": "all", "max-length": 100}},
                {"name": "ha-only", "definition": {"ha-mode": "exactly", "ha-params": 2}},
            ]
        }
        result = apply_transforms(defs, ["strip_cmq_keys", "drop_empty_policies"])
        assert len(result["policies"]) == 1
        assert result["policies"][0]["name"] == "ha"
        assert "ha-mode" not in result["policies"][0]["definition"]
        assert result["policies"][0]["definition"]["max-length"] == 100

    def test_transforms_convert_classic_to_quorum(self):
        defs = {
            "queues": [
                {"name": "q1", "arguments": {"x-queue-type": "classic"}, "durable": False},
                {"name": "q2", "arguments": {"x-queue-type": "quorum"}, "durable": True},
            ]
        }
        result = apply_transforms(defs, ["convert_classic_to_quorum"])
        assert result["queues"][0]["arguments"]["x-queue-type"] == "quorum"
        assert result["queues"][0]["durable"] is True
        assert result["queues"][1]["arguments"]["x-queue-type"] == "quorum"
