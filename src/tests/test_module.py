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

from src.rabbitmq.module import RabbitMQModule


@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    mcp.tool = lambda: lambda f: f
    return mcp


@pytest.fixture
def module(mock_mcp):
    return RabbitMQModule(mock_mcp)


class TestRabbitMQModule:
    def test_init(self, module):
        assert module.rmq is None
        assert module.rmq_admin is None

    def test_register_tools_read_only(self, module):
        module.register_rabbitmq_management_tools(allow_mutative_tools=False)
        assert module.mcp.tool.called

    def test_register_tools_with_mutative(self, module):
        module.register_rabbitmq_management_tools(allow_mutative_tools=True)
        assert module.mcp.tool.called

    @patch("src.rabbitmq.module.RabbitMQConnection")
    @patch("src.rabbitmq.module.RabbitMQAdmin")
    def test_connection_initialization(self, mock_admin_class, mock_conn_class, module):
        mock_admin = MagicMock()
        mock_admin_class.return_value = mock_admin
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn

        module.register_rabbitmq_management_tools()
        # Simulate calling the connection tool
        module.rmq = mock_conn
        module.rmq_admin = mock_admin

        assert module.rmq is not None
        assert module.rmq_admin is not None
