import argparse
import os
import sys

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider
from loguru import logger

from mcp_server_rabbitmq.admin import RabbitMQAdmin
from mcp_server_rabbitmq.connection import RabbitMQConnection, validate_rabbitmq_name
from mcp_server_rabbitmq.constant import MCP_SERVER_VERSION
from mcp_server_rabbitmq.handlers import (
    handle_delete_exchange,
    handle_delete_queue,
    handle_enqueue,
    handle_fanout,
    handle_get_exchange_info,
    handle_get_queue_info,
    handle_list_exchanges,
    handle_list_exchanges_by_vhost,
    handle_list_queues,
    handle_list_queues_by_vhost,
    handle_list_shovels,
    handle_list_vhosts,
    handle_purge_queue,
    handle_shovel,
)


class RabbitMQMCPServer:
    def __init__(
        self,
        rabbitmq_host=None,
        rabbitmq_port=None,
        rabbitmq_username=None,
        rabbitmq_password=None,
        rabbitmq_use_tls=None,
        rabbitmq_api_port=None,
    ):
        # Setup logger
        logger.remove()
        logger.add(sys.stderr, level=os.getenv("FASTMCP_LOG_LEVEL", "WARNING"))
        self.logger = logger

        # Initialize FastMCP
        self.mcp = FastMCP(
            "mcp-server-rabbitmq",
            instructions="""Manage RabbitMQ message brokers and interact with queues and exchanges.""",
        )

        # Connection parameters
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_username = rabbitmq_username
        self.rabbitmq_password = rabbitmq_password
        self.rabbitmq_use_tls = rabbitmq_use_tls
        self.rabbitmq_api_port = rabbitmq_api_port

        # Register tools
        self._register_tools()

    def _register_tools(self):
        @self.mcp.tool()
        def enqueue(queue: str, message: str) -> str:
            """Enqueue a message to a queue hosted on RabbitMQ."""
            validate_rabbitmq_name(queue, "Queue name")
            try:
                rabbitmq = RabbitMQConnection(
                    self.rabbitmq_host,
                    self.rabbitmq_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                handle_enqueue(rabbitmq, queue, message)
                return "Message successfully enqueued"
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to enqueue message: {e}"

        @self.mcp.tool()
        def fanout(exchange: str, message: str) -> str:
            """Publish a message to an exchange with fanout type."""
            validate_rabbitmq_name(exchange, "Exchange name")
            try:
                rabbitmq = RabbitMQConnection(
                    self.rabbitmq_host,
                    self.rabbitmq_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                handle_fanout(rabbitmq, exchange, message)
                return "Message successfully published to exchange"
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to publish message: {e}"

        @self.mcp.tool()
        def publish(topic: str, message: str):
            raise NotImplementedError()

        @self.mcp.tool()
        def list_queues() -> str:
            """List all the queues in the broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_list_queues(admin)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to list queues: {e}"

        @self.mcp.tool()
        def list_queues_by_vhost(vhost: str = "/") -> str:
            """List all the queues for a specific virtual host (vhost) in the broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_list_queues_by_vhost(admin, vhost)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to get queue info: {e}"

        @self.mcp.tool()
        def list_exchanges() -> str:
            """List all the exchanges in the broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_list_exchanges(admin)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to list exchanges: {e}"

        @self.mcp.tool()
        def list_vhosts() -> str:
            """List all the virtual hosts (vhosts) in the broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_list_vhosts(admin)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to list virtual hosts: {e}"

        @self.mcp.tool()
        def list_exchanges_by_vhost(vhost: str = "/") -> str:
            """List all the exchanges for a specific virtual host in the broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_list_exchanges_by_vhost(admin, vhost)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to list exchanges: {e}"

        @self.mcp.tool()
        def get_queue_info(queue: str, vhost: str = "/") -> str:
            """Get detailed information about a specific queue."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                validate_rabbitmq_name(queue, "Queue name")
                result = handle_get_queue_info(admin, queue, vhost)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to get queue info: {e}"

        @self.mcp.tool()
        def delete_queue(queue: str, vhost: str = "/") -> str:
            """Delete a specific queue."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                validate_rabbitmq_name(queue, "Queue name")
                handle_delete_queue(admin, queue, vhost)
                return f"Queue {queue} successfully deleted"
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to delete queue: {e}"

        @self.mcp.tool()
        def purge_queue(queue: str, vhost: str = "/") -> str:
            """Remove all messages from a specific queue."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                validate_rabbitmq_name(queue, "Queue name")
                handle_purge_queue(admin, queue, vhost)
                return f"Queue {queue} successfully purged"
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to purge queue: {e}"

        @self.mcp.tool()
        def delete_exchange(exchange: str, vhost: str = "/") -> str:
            """Delete a specific exchange."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                validate_rabbitmq_name(exchange, "Exchange name")
                handle_delete_exchange(admin, exchange, vhost)
                return f"Exchange {exchange} successfully deleted"
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to delete exchange: {e}"

        @self.mcp.tool()
        def get_exchange_info(exchange: str, vhost: str = "/") -> str:
            """Get detailed information about a specific exchange."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                validate_rabbitmq_name(exchange, "Exchange name")
                result = handle_get_exchange_info(admin, exchange, vhost)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to get exchange info: {e}"

        @self.mcp.tool()
        def list_shovels() -> str:
            """Get detailed information about shovels in the RabbitMQ broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_list_shovels(admin)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to get exchange info: {e}"

        @self.mcp.tool()
        def get_shovel_info(name: str, vhost: str = "/") -> str:
            """Get detailed information about specific shovel by name that is in a selected virtual host (vhost) in the RabbitMQ broker."""
            try:
                admin = RabbitMQAdmin(
                    self.rabbitmq_host,
                    self.rabbitmq_api_port,
                    self.rabbitmq_username,
                    self.rabbitmq_password,
                    self.rabbitmq_use_tls,
                )
                result = handle_shovel(admin, name, vhost)
                return str(result)
            except Exception as e:
                self.logger.error(f"{e}")
                return f"Failed to get exchange info: {e}"

        @self.mcp.tool()
        def initialize_connection_to_new_rabbitmq_broker(
            rabbitmq_host: str,
            rabbitmq_username: str,
            rabbitmq_password: str,
            rabbitmq_use_ttl: bool,
            rabbitmq_api_port: int = 15671,
        ) -> str:
            """It allows user to connect to a new rabbitmq broker that is different than the one the user configures initially during the start of this server"""
            self.rabbitmq_host = rabbitmq_host
            self.rabbitmq_username = rabbitmq_username
            self.rabbitmq_password = rabbitmq_password
            self.rabbitmq_use_tls = rabbitmq_use_ttl
            self.rabbitmq_api_port = rabbitmq_api_port

            return "successfully connected"

    def run(self, args):
        """Run the MCP server with the provided arguments."""
        self.logger.info(f"Starting RabbitMQ MCP Server v{MCP_SERVER_VERSION}")

        if args.http:
            if args.http_auth_jwks_uri == "":
                raise ValueError("Please set --http-auth-jwks-uri")
            # TODO: check if there is a way to set it properly
            self.mcp.auth = BearerAuthProvider(
                jwks_uri=args.http_auth_jwks_uri,
                issuer=args.http_auth_issuer,
                audience=args.http_auth_audience,
                required_scopes=args.http_auth_required_scopes,
            )
            self.mcp.run(
                transport="streamable-http",
                host="127.0.0.1",
                port=args.server_port,
                path="/mcp",
            )
        else:
            self.mcp.run()


def main():
    """Run the MCP server with CLI argument support."""
    parser = argparse.ArgumentParser(
        description="A Model Context Protocol (MCP) server for RabbitMQ"
    )
    # Required arguments
    parser.add_argument("--rabbitmq-host", type=str, required=True, help="RabbitMQ host")
    parser.add_argument("--port", type=int, required=True, help="Port of the RabbitMQ host")
    parser.add_argument("--username", type=str, required=True, help="Username for the connection")
    parser.add_argument("--password", type=str, required=True, help="Password for the connection")
    parser.add_argument(
        "--use-tls", type=bool, default=False, help="Is the connection using TLS/SSL"
    )
    parser.add_argument(
        "--api-port", type=int, default=15671, help="Port for the RabbitMQ management API"
    )
    # Streamable HTTP specific configuration
    parser.add_argument("--http", action="store_true", help="Use Streamable HTTP transport")
    parser.add_argument(
        "--server-port", type=int, default=8888, help="Port to run the MCP server on"
    )
    parser.add_argument(
        "--http-auth-jwks-uri",
        type=str,
        default=None,
        help="JKWS URI for FastMCP Bearer Auth Provider",
    )
    parser.add_argument(
        "--http-auth-issuer",
        type=str,
        default=None,
        help="Issuer for FastMCP Bearer Auth Provider",
    )
    parser.add_argument(
        "--http-auth-audience",
        type=str,
        default=None,
        help="Audience for FastMCP Bearer Auth Provider",
    )
    parser.add_argument(
        "--http-auth-required-scopes",
        nargs="*",
        default=None,
        help="Required scope for FastMCP Bearer Auth Provider",
    )

    args = parser.parse_args()

    # Create server with connection parameters from args
    server = RabbitMQMCPServer(
        rabbitmq_host=args.rabbitmq_host,
        rabbitmq_port=args.port,
        rabbitmq_username=args.username,
        rabbitmq_password=args.password,
        rabbitmq_use_tls=args.use_tls,
        rabbitmq_api_port=args.api_port,
    )

    # Run the server with remaining args
    server.run(args)


if __name__ == "__main__":
    main()
