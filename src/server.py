## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: Apache-2.0

import argparse
import os
import sys

from mcp.server.fastmcp import FastMCP
from loguru import logger

from .auth import JWKSBearerVerifier

from .constant import MCP_SERVER_VERSION
from .rabbitmq.compat_v3 import register_v3_compat_tools
from .rabbitmq.module import RabbitMQModule
from .rabbitmq.module_v4 import RabbitMQModuleV4, TOOL_GROUPS


class RabbitMQMCPServer:
    def __init__(
        self,
        allow_mutative_tools: bool,
        management_port: int | None = None,
        use_v4: bool = False,
        tool_groups: tuple[str, ...] | None = None,
        v1_compat: bool = False,
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

        if use_v4:
            groups = tool_groups or (
                ("core", "read", "observability", "health")
                if not allow_mutative_tools
                else TOOL_GROUPS
            )
            module = RabbitMQModuleV4(self.mcp)
            module.default_management_port = management_port
            module.register_tools(groups)
            self.logger.info(f"v4 mode: {len(groups)} groups loaded: {groups}")
            if v1_compat:
                register_v3_compat_tools(self.mcp, module)
                self.logger.info("v1-compat: registered deprecated v3 tool aliases")
        else:
            rmq_module = RabbitMQModule(self.mcp)
            rmq_module.default_management_port = management_port
            rmq_module.register_rabbitmq_management_tools(allow_mutative_tools)

    def run(self, args):
        """Run the MCP server with the provided arguments."""
        self.logger.info(f"Starting RabbitMQ MCP Server v{MCP_SERVER_VERSION}")

        if args.http:
            if not args.http_auth_jwks_uri:
                raise ValueError("Please set --http-auth-jwks-uri")
            self.mcp.auth = JWKSBearerVerifier(
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
    parser.add_argument(
        "--v4",
        action="store_true",
        help="Use v4 consolidated tools (28 tools instead of 59). Breaking change from v3.",
    )
    parser.add_argument(
        "--v1-compat",
        action="store_true",
        help="(v4 only) Register deprecated v3 tool names as aliases for backward compatibility",
    )
    parser.add_argument(
        "--tool-groups",
        nargs="*",
        choices=list(TOOL_GROUPS),
        default=None,
        help="(v4 only) Selectively load tool groups: core, read, mutative, migration, observability, health",
    )
    # Streamable HTTP specific configuration
    parser.add_argument("--http", action="store_true", help="Use Streamable HTTP transport")
    parser.add_argument(
        "--server-port", type=int, default=8888, help="Port to run the MCP server on"
    )
    parser.add_argument(
        "--management-port",
        type=int,
        default=None,
        help="Default RabbitMQ Management API port (default: 443 for TLS, 15672 for non-TLS)",
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
    tool_groups = tuple(args.tool_groups) if args.tool_groups else None
    server = RabbitMQMCPServer(
        args.allow_mutative_tools,
        args.management_port,
        use_v4=args.v4,
        tool_groups=tool_groups,
        v1_compat=args.v1_compat,
    )

    # Run the server with remaining args
    server.run(args)


if __name__ == "__main__":
    main()
