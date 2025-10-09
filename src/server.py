## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: Apache-2.0

import argparse
import os
import sys

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider
from loguru import logger

from .constant import MCP_SERVER_VERSION
from .rabbitmq.module import RabbitMQModule


class RabbitMQMCPServer:
    def __init__(self, allow_mutative_tools: bool):
        # Setup logger
        logger.remove()
        logger.add(sys.stderr, level=os.getenv("FASTMCP_LOG_LEVEL", "WARNING"))
        self.logger = logger

        # Initialize FastMCP
        self.mcp = FastMCP(
            "mcp-server-rabbitmq",
            instructions="""Manage RabbitMQ message brokers and interact with queues and exchanges.""",
        )

        rmq_module = RabbitMQModule(self.mcp)
        rmq_module.register_rabbitmq_management_tools(allow_mutative_tools)

    def run(self, args):
        """Run the MCP server with the provided arguments."""
        self.logger.info(f"Starting RabbitMQ MCP Server v{MCP_SERVER_VERSION}")

        if args.http:
            if args.http_auth_jwks_uri == "":
                raise ValueError("Please set --http-auth-jwks-uri")
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
    parser.add_argument(
        "--allow-mutative-tools",
        action="store_true",
        help="Enable tools that can mutate the states of RabbitMQ",
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
    server = RabbitMQMCPServer(args.allow_mutative_tools)

    # Run the server with remaining args
    server.run(args)


if __name__ == "__main__":
    main()
