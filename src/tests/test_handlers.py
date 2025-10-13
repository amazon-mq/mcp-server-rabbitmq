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

from unittest.mock import MagicMock

import pytest

from src.rabbitmq.handlers import (
    handle_delete_exchange,
    handle_delete_queue,
    handle_get_cluster_nodes,
    handle_get_definition,
    handle_get_exchange_info,
    handle_get_guidelines,
    handle_get_queue_info,
    handle_is_broker_in_alarm,
    handle_is_node_in_quorum_critical,
    handle_list_connections,
    handle_list_consumers,
    handle_list_exchanges,
    handle_list_queues,
    handle_list_shovels,
    handle_list_users,
    handle_list_vhosts,
    handle_purge_queue,
    handle_shovel,
)


@pytest.fixture
def mock_admin():
    admin = MagicMock()
    admin.list_queues.return_value = [{"name": "queue1"}, {"name": "queue2"}]
    admin.list_exchanges.return_value = [{"name": "exchange1"}]
    admin.list_vhosts.return_value = [{"name": "vhost1"}]
    admin.get_queue_info.return_value = {"name": "queue1", "messages": 10}
    admin.get_exchange_info.return_value = {"name": "exchange1", "type": "direct"}
    admin.get_alarm_status.return_value = 200
    admin.get_is_node_quorum_critical.return_value = 200
    admin.get_broker_definition.return_value = {"queues": []}
    admin.list_shovels.return_value = [{"name": "shovel1"}]
    admin.get_shovel_info.return_value = {"name": "shovel1"}
    admin.list_connections.return_value = [
        {
            "auth_mechanism": "PLAIN",
            "channels": 1,
            "client_properties": {},
            "connected_at": 1000000,
            "state": "running",
        }
    ]
    admin.list_consumers.return_value = [{"queue": "queue1"}]
    admin.list_users.return_value = [{"name": "user1"}]
    admin.get_cluster_nodes.return_value = [
        {
            "name": "node1",
            "mem_alarm": False,
            "disk_free_alarm": False,
            "disk_free": 1000,
            "mem_limit": 2000,
            "mem_used": 1000,
            "rates_mode": "basic",
            "uptime": 10000,
            "running": True,
            "queue_created": 5,
            "queue_deleted": 1,
            "connection_created": 10,
        }
    ]
    return admin


class TestHandlers:
    def test_handle_list_queues(self, mock_admin):
        result = handle_list_queues(mock_admin)
        assert result == ["queue1", "queue2"]

    def test_handle_list_exchanges(self, mock_admin):
        result = handle_list_exchanges(mock_admin)
        assert result == ["exchange1"]

    def test_handle_list_vhosts(self, mock_admin):
        result = handle_list_vhosts(mock_admin)
        assert result == ["vhost1"]

    def test_handle_get_queue_info(self, mock_admin):
        result = handle_get_queue_info(mock_admin, "queue1")
        assert result == {"name": "queue1", "messages": 10}

    def test_handle_get_exchange_info(self, mock_admin):
        result = handle_get_exchange_info(mock_admin, "exchange1")
        assert result == {"name": "exchange1", "type": "direct"}

    def test_handle_delete_queue(self, mock_admin):
        handle_delete_queue(mock_admin, "queue1")
        mock_admin.delete_queue.assert_called_once_with("queue1", "/")

    def test_handle_purge_queue(self, mock_admin):
        handle_purge_queue(mock_admin, "queue1")
        mock_admin.purge_queue.assert_called_once_with("queue1", "/")

    def test_handle_delete_exchange(self, mock_admin):
        handle_delete_exchange(mock_admin, "exchange1")
        mock_admin.delete_exchange.assert_called_once_with("exchange1", "/")

    def test_handle_is_broker_in_alarm_false(self, mock_admin):
        result = handle_is_broker_in_alarm(mock_admin)
        assert result is False

    def test_handle_is_broker_in_alarm_true(self, mock_admin):
        mock_admin.get_alarm_status.return_value = 500
        result = handle_is_broker_in_alarm(mock_admin)
        assert result is True

    def test_handle_is_node_in_quorum_critical_false(self, mock_admin):
        result = handle_is_node_in_quorum_critical(mock_admin)
        assert result is False

    def test_handle_is_node_in_quorum_critical_true(self, mock_admin):
        mock_admin.get_is_node_quorum_critical.return_value = 500
        result = handle_is_node_in_quorum_critical(mock_admin)
        assert result is True

    def test_handle_get_definition(self, mock_admin):
        result = handle_get_definition(mock_admin)
        assert result == {"queues": []}

    def test_handle_list_shovels(self, mock_admin):
        result = handle_list_shovels(mock_admin)
        assert result == [{"name": "shovel1"}]

    def test_handle_shovel(self, mock_admin):
        result = handle_shovel(mock_admin, "shovel1")
        assert result == {"name": "shovel1"}

    def test_handle_list_connections(self, mock_admin):
        result = handle_list_connections(mock_admin)
        assert len(result) == 1
        assert result[0]["auth_mechanism"] == "PLAIN"

    def test_handle_list_consumers(self, mock_admin):
        result = handle_list_consumers(mock_admin)
        assert result == [{"queue": "queue1"}]

    def test_handle_list_users(self, mock_admin):
        result = handle_list_users(mock_admin)
        assert result == [{"name": "user1"}]

    def test_handle_get_cluster_nodes(self, mock_admin):
        result = handle_get_cluster_nodes(mock_admin)
        assert len(result) == 1
        assert result[0]["name"] == "node1"
        assert result[0]["mem_used_in_percentage"] == 50.0

    def test_handle_get_guidelines_valid(self):
        result = handle_get_guidelines("rabbimq_broker_sizing_guide")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handle_get_guidelines_invalid(self):
        with pytest.raises(ValueError, match="doesn't exist"):
            handle_get_guidelines("invalid_guide")
