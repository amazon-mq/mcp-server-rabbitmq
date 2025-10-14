"""Strands agent that uses RabbitMQ MCP server via stdio."""

from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to RabbitMQ MCP server using stdio transport
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="/Users/qrl/.local/bin/uvx",
        args=["amq-mcp-server-rabbitmq@latest"]
    )
))

# Create an agent with MCP tools
with stdio_mcp_client:
    tools = stdio_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    agent("what can you do?")
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input or user_input.lower() in ["exit", "quit"]:
            break
        agent(user_input)
