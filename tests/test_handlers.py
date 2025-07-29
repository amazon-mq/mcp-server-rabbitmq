"""Tests for the RabbitMQ handlers module."""

from unittest.mock import MagicMock, patch

from mcp_server_rabbitmq.handlers import (
    handle_delete_exchange,
    handle_delete_queue,
    handle_enqueue,
    handle_fanout,
    handle_get_exchange_info,
    handle_get_queue_info,
    handle_list_exchanges,
    handle_list_queues,
    handle_purge_queue,
)


class TestQueueHandlers:
    """Test the queue-related handler functions."""

    @patch("mcp_server_rabbitmq.handlers.RabbitMQConnection")
    def test_handle_enqueue(self, mock_connection_class):
        """Test that handle_enqueue correctly publishes a message to a queue."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.get_channel.return_value = (mock_connection, mock_channel)

        # Call the function
        handle_enqueue(mock_connection, "test-queue", "test-message")

        # Verify the expected calls were made
        mock_connection.get_channel.assert_called_once()
        mock_channel.queue_declare.assert_called_once_with("test-queue")
        mock_channel.basic_publish.assert_called_once_with(
            exchange="", routing_key="test-queue", body="test-message"
        )
        mock_connection.close.assert_called_once()

    @patch("mcp_server_rabbitmq.handlers.RabbitMQConnection")
    def test_handle_fanout(self, mock_connection_class):
        """Test that handle_fanout correctly publishes a message to an exchange."""
        # Setup mocks
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.get_channel.return_value = (mock_connection, mock_channel)

        # Call the function
        handle_fanout(mock_connection, "test-exchange", "test-message")

        # Verify the expected calls were made
        mock_connection.get_channel.assert_called_once()
        mock_channel.exchange_declare.assert_called_once_with(
            exchange="test-exchange", exchange_type="fanout"
        )
        mock_channel.basic_publish.assert_called_once_with(
            exchange="test-exchange", routing_key="", body="test-message"
        )
        mock_connection.close.assert_called_once()

    def test_handle_list_queues(self):
        """Test that handle_list_queues correctly returns queue names."""
        # Setup mock
        mock_admin = MagicMock()
        mock_admin.list_queues.return_value = [
            {"name": "queue1", "other_field": "value1"},
            {"name": "queue2", "other_field": "value2"},
        ]

        # Call the function
        result = handle_list_queues(mock_admin)

        # Verify the result
        assert result == ["queue1", "queue2"]
        mock_admin.list_queues.assert_called_once()

    def test_handle_list_exchanges(self):
        """Test that handle_list_exchanges correctly returns exchange names."""
        # Setup mock
        mock_admin = MagicMock()
        mock_admin.list_exchanges.return_value = [
            {"name": "exchange1", "other_field": "value1"},
            {"name": "exchange2", "other_field": "value2"},
        ]

        # Call the function
        result = handle_list_exchanges(mock_admin)

        # Verify the result
        assert result == ["exchange1", "exchange2"]
        mock_admin.list_exchanges.assert_called_once()

    def test_handle_get_queue_info(self):
        """Test that handle_get_queue_info correctly returns queue information."""
        # Setup mock
        mock_admin = MagicMock()
        expected_result = {"name": "test-queue", "messages": 10, "consumers": 2}
        mock_admin.get_queue_info.return_value = expected_result

        # Call the function with default vhost
        result = handle_get_queue_info(mock_admin, "test-queue")

        # Verify the result
        assert result == expected_result
        mock_admin.get_queue_info.assert_called_once_with("test-queue", "/")

        # Reset mock and test with custom vhost
        mock_admin.reset_mock()
        result = handle_get_queue_info(mock_admin, "test-queue", "custom-vhost")

        # Verify the result
        assert result == expected_result
        mock_admin.get_queue_info.assert_called_once_with("test-queue", "custom-vhost")

    def test_handle_delete_queue(self):
        """Test that handle_delete_queue correctly calls the admin method."""
        # Setup mock
        mock_admin = MagicMock()

        # Call the function with default vhost
        handle_delete_queue(mock_admin, "test-queue")

        # Verify the call
        mock_admin.delete_queue.assert_called_once_with("test-queue", "/")

        # Reset mock and test with custom vhost
        mock_admin.reset_mock()
        handle_delete_queue(mock_admin, "test-queue", "custom-vhost")

        # Verify the call
        mock_admin.delete_queue.assert_called_once_with("test-queue", "custom-vhost")

    def test_handle_purge_queue(self):
        """Test that handle_purge_queue correctly calls the admin method."""
        # Setup mock
        mock_admin = MagicMock()

        # Call the function with default vhost
        handle_purge_queue(mock_admin, "test-queue")

        # Verify the call
        mock_admin.purge_queue.assert_called_once_with("test-queue", "/")

        # Reset mock and test with custom vhost
        mock_admin.reset_mock()
        handle_purge_queue(mock_admin, "test-queue", "custom-vhost")

        # Verify the call
        mock_admin.purge_queue.assert_called_once_with("test-queue", "custom-vhost")


class TestExchangeHandlers:
    """Test the exchange-related handler functions."""

    def test_handle_delete_exchange(self):
        """Test that handle_delete_exchange correctly calls the admin method."""
        # Setup mock
        mock_admin = MagicMock()

        # Call the function with default vhost
        handle_delete_exchange(mock_admin, "test-exchange")

        # Verify the call
        mock_admin.delete_exchange.assert_called_once_with("test-exchange", "/")

        # Reset mock and test with custom vhost
        mock_admin.reset_mock()
        handle_delete_exchange(mock_admin, "test-exchange", "custom-vhost")

        # Verify the call
        mock_admin.delete_exchange.assert_called_once_with("test-exchange", "custom-vhost")

    def test_handle_get_exchange_info(self):
        """Test that handle_get_exchange_info correctly returns exchange information."""
        # Setup mock
        mock_admin = MagicMock()
        expected_result = {"name": "test-exchange", "type": "fanout", "durable": True}
        mock_admin.get_exchange_info.return_value = expected_result

        # Call the function with default vhost
        result = handle_get_exchange_info(mock_admin, "test-exchange")

        # Verify the result
        assert result == expected_result
        mock_admin.get_exchange_info.assert_called_once_with("test-exchange", "/")

        # Reset mock and test with custom vhost
        mock_admin.reset_mock()
        result = handle_get_exchange_info(mock_admin, "test-exchange", "custom-vhost")

        # Verify the result
        assert result == expected_result
        mock_admin.get_exchange_info.assert_called_once_with("test-exchange", "custom-vhost")
