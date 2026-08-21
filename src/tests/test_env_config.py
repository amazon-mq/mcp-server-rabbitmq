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

from src.rabbitmq.env_config import (
    _AMQP_SCHEMES,
    _MANAGEMENT_SCHEMES,
    ALIAS_ENV,
    AMQP_ENDPOINT_ENV,
    MANAGEMENT_ENDPOINT_ENV,
    auto_connect_from_env,
    parse_endpoint,
)
from src.rabbitmq.module import RabbitMQModule
from src.rabbitmq.module_v4 import RabbitMQModuleV4

# Both tool layouts must behave identically. Parametrizing here is what keeps
# the v4 path from silently missing the feature.
MODULE_CLASSES = [RabbitMQModule, RabbitMQModuleV4]


@pytest.fixture(params=MODULE_CLASSES, ids=["v3", "v4"])
def module(request):
    return request.param(MagicMock())


class TestParseEndpoint:
    @pytest.mark.parametrize(
        "uri,expected_port,expected_tls",
        [
            ("amqps://u:p@host", 5671, True),
            ("amqp://u:p@host", 5672, False),
            ("amqps://u:p@host:5555", 5555, True),
            ("amqp://u:p@host:5555", 5555, False),
        ],
    )
    def test_amqp_scheme_sets_tls_and_default_port(self, uri, expected_port, expected_tls):
        endpoint = parse_endpoint(uri, _AMQP_SCHEMES, AMQP_ENDPOINT_ENV)
        assert endpoint.port == expected_port
        assert endpoint.use_tls is expected_tls
        assert endpoint.hostname == "host"

    @pytest.mark.parametrize(
        "uri,expected_port,expected_tls",
        [
            ("https://u:p@host", 443, True),
            ("http://u:p@host", 15672, False),
            ("https://u:p@host:15671", 15671, True),
        ],
    )
    def test_management_scheme_sets_tls_and_default_port(self, uri, expected_port, expected_tls):
        endpoint = parse_endpoint(uri, _MANAGEMENT_SCHEMES, MANAGEMENT_ENDPOINT_ENV)
        assert endpoint.port == expected_port
        assert endpoint.use_tls is expected_tls

    def test_percent_encoded_credentials_are_decoded(self):
        endpoint = parse_endpoint("amqps://us%40er:p%40ss%2Fword@host", _AMQP_SCHEMES, "V")
        assert endpoint.username == "us@er"
        assert endpoint.password == "p@ss/word"

    def test_credentials_are_not_in_safe_display(self):
        endpoint = parse_endpoint("amqps://user:sup3rsecret@host:5671", _AMQP_SCHEMES, "V")
        assert endpoint.safe_display == "amqps://host:5671"
        assert "sup3rsecret" not in endpoint.safe_display

    @pytest.mark.parametrize(
        "uri,match",
        [
            ("http://u:p@host", "must start with"),  # management scheme in the AMQP slot
            ("amqps://host", "must include credentials"),
            ("amqps://u@host", "must include credentials"),
            ("amqps://u:p@host:notaport", "non-numeric port"),
            ("amqps://u:p@", "missing a hostname"),
        ],
    )
    def test_rejects_bad_uris(self, uri, match):
        with pytest.raises(ValueError, match=match):
            parse_endpoint(uri, _AMQP_SCHEMES, AMQP_ENDPOINT_ENV)

    def test_error_message_never_leaks_the_password(self):
        with pytest.raises(ValueError) as excinfo:
            parse_endpoint("ftp://user:sup3rsecret@host", _AMQP_SCHEMES, AMQP_ENDPOINT_ENV)
        assert "sup3rsecret" not in str(excinfo.value)


class TestAutoConnectFromEnv:
    def test_no_env_vars_is_a_no_op(self, module):
        assert auto_connect_from_env(module, env={}) is False
        assert module.brokers == {}
        assert module.active_alias is None

    def test_registers_and_activates_broker(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection") as conn,
            patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
        ):
            result = auto_connect_from_env(
                module, env={AMQP_ENDPOINT_ENV: "amqps://user:pass@broker.example.com:5671"}
            )

        assert result is True
        assert module.active_alias == "broker.example.com"
        assert module.brokers["broker.example.com"]["hostname"] == "broker.example.com"
        admin.return_value.test_connection.assert_called_once()
        assert conn.call_args.kwargs == {
            "hostname": "broker.example.com",
            "username": "user",
            "password": "pass",
            "port": 5671,
            "use_tls": True,
        }

    def test_alias_env_overrides_hostname(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection"),
            patch("src.rabbitmq.env_config.RabbitMQAdmin"),
        ):
            auto_connect_from_env(
                module,
                env={
                    AMQP_ENDPOINT_ENV: "amqps://user:pass@broker.example.com",
                    ALIAS_ENV: "prod",
                },
            )

        assert module.active_alias == "prod"
        assert "prod" in module.brokers

    def test_management_endpoint_derived_from_amqp(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection"),
            patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
        ):
            auto_connect_from_env(
                module, env={AMQP_ENDPOINT_ENV: "amqps://user:pass@broker.example.com"}
            )

        assert admin.call_args.kwargs["port"] == 443
        assert admin.call_args.kwargs["use_tls"] is True
        assert admin.call_args.kwargs["hostname"] == "broker.example.com"

    def test_derived_management_endpoint_is_plaintext_for_amqp(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection"),
            patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
        ):
            auto_connect_from_env(module, env={AMQP_ENDPOINT_ENV: "amqp://user:pass@localhost"})

        assert admin.call_args.kwargs["port"] == 15672
        assert admin.call_args.kwargs["use_tls"] is False

    def test_management_port_cli_arg_wins_over_scheme_default(self, module):
        module.default_management_port = 15671
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection"),
            patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
        ):
            auto_connect_from_env(
                module, env={AMQP_ENDPOINT_ENV: "amqps://user:pass@broker.example.com"}
            )

        assert admin.call_args.kwargs["port"] == 15671

    def test_explicit_management_endpoint_wins(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection"),
            patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
        ):
            auto_connect_from_env(
                module,
                env={
                    AMQP_ENDPOINT_ENV: "amqps://user:pass@broker.example.com",
                    MANAGEMENT_ENDPOINT_ENV: "https://mgmtuser:mgmtpass@mgmt.example.com:8443",
                },
            )

        assert admin.call_args.kwargs["hostname"] == "mgmt.example.com"
        assert admin.call_args.kwargs["username"] == "mgmtuser"
        assert admin.call_args.kwargs["port"] == 8443

    def test_amqp_endpoint_derived_from_management_only(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection") as conn,
            patch("src.rabbitmq.env_config.RabbitMQAdmin"),
        ):
            result = auto_connect_from_env(
                module,
                env={MANAGEMENT_ENDPOINT_ENV: "https://user:pass@broker.example.com:443"},
            )

        assert result is True
        assert conn.call_args.kwargs["port"] == 5671
        assert conn.call_args.kwargs["use_tls"] is True

    def test_unreachable_broker_warns_and_leaves_registry_empty(self, module):
        with (
            patch("src.rabbitmq.env_config.RabbitMQConnection"),
            patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
        ):
            admin.return_value.test_connection.side_effect = OSError("connection refused")
            result = auto_connect_from_env(
                module, env={AMQP_ENDPOINT_ENV: "amqps://user:pass@broker.example.com"}
            )

        assert result is False
        assert module.brokers == {}
        assert module.active_alias is None

    def test_malformed_endpoint_is_skipped_not_raised(self, module):
        result = auto_connect_from_env(module, env={AMQP_ENDPOINT_ENV: "not-a-uri"})
        assert result is False
        assert module.brokers == {}

    def test_failure_log_does_not_leak_the_password(self, module, capsys):
        from loguru import logger

        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="DEBUG")
        try:
            with (
                patch("src.rabbitmq.env_config.RabbitMQConnection"),
                patch("src.rabbitmq.env_config.RabbitMQAdmin") as admin,
            ):
                admin.return_value.test_connection.side_effect = OSError("refused")
                auto_connect_from_env(
                    module,
                    env={AMQP_ENDPOINT_ENV: "amqps://user:sup3rsecret@broker.example.com"},
                )
        finally:
            logger.remove()

        assert "sup3rsecret" not in capsys.readouterr().out

    def test_success_log_does_not_leak_the_password(self, module, capsys):
        from loguru import logger

        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="DEBUG")
        try:
            with (
                patch("src.rabbitmq.env_config.RabbitMQConnection"),
                patch("src.rabbitmq.env_config.RabbitMQAdmin"),
            ):
                auto_connect_from_env(
                    module,
                    env={AMQP_ENDPOINT_ENV: "amqps://user:sup3rsecret@broker.example.com"},
                )
        finally:
            logger.remove()

        assert "sup3rsecret" not in capsys.readouterr().out
