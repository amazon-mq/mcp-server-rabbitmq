"""Tests for the RabbitMQ connection module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server_rabbitmq.connection import RabbitMQConnection, validate_rabbitmq_name


class TestRabbitMQConnection:
    """Test the RabbitMQConnection class."""

    @patch("mcp_server_rabbitmq.connection.pika.BlockingConnection")
    def test_connection_initialization(self, mock_connection):
        """Test that the connection is initialized correctly."""
        mock_connection.return_value = MagicMock()
        connection = RabbitMQConnection("localhost", 5672, "guest", "guest", False)
        assert connection is not None
        _, _ = connection.get_channel()
        mock_connection.assert_called_once()


class TestValidation:
    """Test the validation functions."""

    def test_validate_rabbitmq_name_valid(self):
        """Test that valid names pass validation."""
        # These should not raise exceptions
        validate_rabbitmq_name("valid-name", "Test")
        validate_rabbitmq_name("valid_name", "Test")
        validate_rabbitmq_name("valid.name", "Test")
        validate_rabbitmq_name("valid123", "Test")

    def test_validate_rabbitmq_name_invalid(self):
        """Test that invalid names fail validation."""
        with pytest.raises(ValueError):
            validate_rabbitmq_name("", "Test")

        with pytest.raises(ValueError):
            validate_rabbitmq_name("invalid/name", "Test")

        with pytest.raises(ValueError):
            validate_rabbitmq_name("invalid\\name", "Test")

        with pytest.raises(ValueError):
            validate_rabbitmq_name("invalid*name", "Test")
