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

import pytest

from src.rabbitmq.connection import RabbitMQConnection, validate_rabbitmq_name


class TestRabbitMQConnection:
    def test_init_with_tls(self):
        conn = RabbitMQConnection("localhost", "user", "pass", use_tls=True)
        assert conn.protocol == "amqps"
        assert "amqps://user:pass@localhost:5671" == conn.url

    def test_init_without_tls(self):
        conn = RabbitMQConnection("localhost", "user", "pass", use_tls=False)
        assert conn.protocol == "amqp"
        assert "amqp://user:pass@localhost:5671" == conn.url


class TestValidateRabbitMQName:
    def test_valid_names(self):
        validate_rabbitmq_name("valid-queue", "Queue")
        validate_rabbitmq_name("valid_queue", "Queue")
        validate_rabbitmq_name("valid.queue", "Queue")
        validate_rabbitmq_name("valid:queue", "Queue")
        validate_rabbitmq_name("queue123", "Queue")

    def test_empty_name(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_rabbitmq_name("", "Queue")

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_rabbitmq_name("   ", "Queue")

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="can only contain"):
            validate_rabbitmq_name("invalid@queue", "Queue")

    def test_too_long(self):
        with pytest.raises(ValueError, match="must be less than 255"):
            validate_rabbitmq_name("a" * 256, "Queue")
