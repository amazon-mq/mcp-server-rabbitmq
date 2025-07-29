"""Tests for the RabbitMQ MCP Server with streamable HTTP support."""

import unittest
from unittest.mock import MagicMock, patch

from mcp_server_rabbitmq.server import RabbitMQMCPServer


class TestRabbitMQMCPServer(unittest.TestCase):
    """Test the RabbitMQMCPServer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = RabbitMQMCPServer(
            rabbitmq_host="test-host",
            rabbitmq_port=5672,
            rabbitmq_username="test-user",
            rabbitmq_password="test-pass",
            rabbitmq_use_tls=False,
            rabbitmq_api_port=15672,
        )

    @patch("mcp_server_rabbitmq.server.FastMCP")
    def test_server_initialization(self, mock_fastmcp):
        """Test that the server initializes correctly."""
        server = RabbitMQMCPServer(
            rabbitmq_host="test-host",
            rabbitmq_port=5672,
            rabbitmq_username="test-user",
            rabbitmq_password="test-pass",
            rabbitmq_use_tls=False,
            rabbitmq_api_port=15672,
        )

        # Verify FastMCP was initialized correctly
        mock_fastmcp.assert_called_once_with(
            "mcp-server-rabbitmq",
            instructions="Manage RabbitMQ message brokers and interact with queues and exchanges.",
        )

        # Verify connection parameters were stored
        self.assertEqual(server.rabbitmq_host, "test-host")
        self.assertEqual(server.rabbitmq_port, 5672)
        self.assertEqual(server.rabbitmq_username, "test-user")
        self.assertEqual(server.rabbitmq_password, "test-pass")
        self.assertEqual(server.rabbitmq_use_tls, False)
        self.assertEqual(server.rabbitmq_api_port, 15672)

    @patch("mcp_server_rabbitmq.server.BearerAuthProvider")
    @patch("mcp_server_rabbitmq.server.FastMCP")
    def test_run_with_streamable_http(self, mock_fastmcp, mock_bearer_auth):
        """Test that the server runs with streamable HTTP transport."""
        # Create a mock FastMCP instance
        mock_mcp_instance = MagicMock()
        mock_fastmcp.return_value = mock_mcp_instance

        # Create a mock BearerAuthProvider instance
        mock_auth_provider = MagicMock()
        mock_bearer_auth.return_value = mock_auth_provider

        # Create server instance
        server = RabbitMQMCPServer(
            rabbitmq_host="test-host",
            rabbitmq_port=5672,
            rabbitmq_username="test-user",
            rabbitmq_password="test-pass",
            rabbitmq_use_tls=False,
            rabbitmq_api_port=15672,
        )

        # Create mock args for HTTP mode
        args = MagicMock()
        args.http = True
        args.http_auth_jwks_uri = "https://example.com/jwks"
        args.http_auth_issuer = "test-issuer"
        args.http_auth_audience = "test-audience"
        args.http_auth_required_scopes = ["test-scope"]
        args.server_port = 8888

        # Run the server
        server.run(args)

        # Verify BearerAuthProvider was initialized correctly
        mock_bearer_auth.assert_called_once_with(
            jwks_uri="https://example.com/jwks",
            issuer="test-issuer",
            audience="test-audience",
            required_scopes=["test-scope"],
        )

        # Verify auth provider was set
        self.assertEqual(mock_mcp_instance.auth, mock_auth_provider)

        # Verify run was called with streamable-http transport
        mock_mcp_instance.run.assert_called_once_with(
            transport="streamable-http",
            host="127.0.0.1",
            port=8888,
            path="/mcp",
        )

    @patch("mcp_server_rabbitmq.server.FastMCP")
    def test_run_without_http(self, mock_fastmcp):
        """Test that the server runs with default transport."""
        # Create a mock FastMCP instance
        mock_mcp_instance = MagicMock()
        mock_fastmcp.return_value = mock_mcp_instance

        # Create server instance
        server = RabbitMQMCPServer(
            rabbitmq_host="test-host",
            rabbitmq_port=5672,
            rabbitmq_username="test-user",
            rabbitmq_password="test-pass",
            rabbitmq_use_tls=False,
            rabbitmq_api_port=15672,
        )

        # Create mock args for non-HTTP mode
        args = MagicMock()
        args.http = False

        # Run the server
        server.run(args)

        # Verify run was called with default transport
        mock_mcp_instance.run.assert_called_once_with()

    @patch("mcp_server_rabbitmq.server.FastMCP")
    def test_run_with_http_missing_jwks_uri(self, mock_fastmcp):
        """Test that the server raises an error when JWKS URI is missing."""
        # Create server instance
        server = RabbitMQMCPServer(
            rabbitmq_host="test-host",
            rabbitmq_port=5672,
            rabbitmq_username="test-user",
            rabbitmq_password="test-pass",
            rabbitmq_use_tls=False,
            rabbitmq_api_port=15672,
        )

        # Create mock args with missing JWKS URI
        args = MagicMock()
        args.http = True
        args.http_auth_jwks_uri = ""

        # Verify that running the server raises a ValueError
        with self.assertRaises(ValueError) as context:
            server.run(args)

        self.assertEqual(str(context.exception), "Please set --http-auth-jwks-uri")


if __name__ == "__main__":
    unittest.main()
