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

from unittest.mock import MagicMock, patch

import pytest

from src.rabbitmq.admin import RabbitMQAdmin


@pytest.fixture
def admin():
    return RabbitMQAdmin("localhost", "user", "pass")


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"test": "data"}
    return response


class TestRabbitMQAdmin:
    def test_init(self, admin):
        assert admin.protocol == "https"
        assert admin.base_url == "https://localhost/api"

    @patch("src.rabbitmq.admin.requests.request")
    def test_list_queues(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.list_queues()
        assert result == {"test": "data"}
        mock_request.assert_called_once()

    @patch("src.rabbitmq.admin.requests.request")
    def test_get_queue_info(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.get_queue_info("test-queue")
        assert result == {"test": "data"}

    @patch("src.rabbitmq.admin.requests.request")
    def test_delete_queue(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        admin.delete_queue("test-queue")
        mock_request.assert_called_once()

    @patch("src.rabbitmq.admin.requests.request")
    def test_purge_queue(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        admin.purge_queue("test-queue")
        mock_request.assert_called_once()

    @patch("src.rabbitmq.admin.requests.request")
    def test_list_exchanges(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.list_exchanges()
        assert result == {"test": "data"}

    @patch("src.rabbitmq.admin.requests.request")
    def test_get_exchange_info(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.get_exchange_info("test-exchange")
        assert result == {"test": "data"}

    @patch("src.rabbitmq.admin.requests.request")
    def test_delete_exchange(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        admin.delete_exchange("test-exchange")
        mock_request.assert_called_once()

    @patch("src.rabbitmq.admin.requests.request")
    def test_get_overview(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.get_overview()
        assert result == {"test": "data"}

    @patch("src.rabbitmq.admin.requests.request")
    def test_list_vhosts(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.list_vhosts()
        assert result == {"test": "data"}

    @patch("src.rabbitmq.admin.requests.request")
    def test_get_alarm_status(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.get_alarm_status()
        assert result == 200

    @patch("src.rabbitmq.admin.requests.request")
    def test_get_broker_definition(self, mock_request, admin, mock_response):
        mock_request.return_value = mock_response
        result = admin.get_broker_definition()
        assert result == {"test": "data"}
