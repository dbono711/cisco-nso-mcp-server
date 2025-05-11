#!/usr/bin/env python3
"""
Sample STDIO client for Cisco NSO MCP Server

This script demonstrates how to connect to the MCP server and list available tools.
"""
import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    print("Connecting to MCP server...")

    # create server parameters
    server_params = StdioServerParameters(
        command="cisco-nso-mcp-server",
        args=[],
        env={**os.environ}
    )

    # create and enter the context managers directly in this task
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:

            # initialize the session
            await session.initialize()

            # list available tools
            tools_response = await session.list_tools()
            print("\nAvailable tools:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            ned_response = await session.call_tool("get_device_ned_ids_tool")
            print("\nNED IDs:")
            print(ned_response.content[0].text)

            print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())