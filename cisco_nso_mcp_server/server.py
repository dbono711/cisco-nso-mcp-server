#!/usr/bin/env python3
"""
Cisco NSO MCP Server

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO via RESTCONF.
"""
from cisco_nso_restconf.client import NSORestconfClient
from cisco_nso_restconf.devices import Devices
from cisco_nso_restconf.query import Query
from mcp.server.fastmcp import FastMCP
from cisco_nso_mcp_server.services.environment import get_environment_summary
from cisco_nso_mcp_server.services.devices import get_device_platform, get_device_ned_ids
from typing import Optional, Dict, Any
from cisco_nso_mcp_server.utils import logger


def register_resources(mcp, query_helper):
    @mcp.resource(
        uri="https://cisco-nso-mcp-server.bonolab.net/resources/environment",
        description="NSO environment summary",
    )
    async def nso_environment():
        try:
            # delegate to the service layer
            return await get_environment_summary(query_helper)
            
        except Exception as e:
            logger.error(f"Resource error: {str(e)}")

            return {
                "status": "error",
                "error_message": str(e)
            }

def register_tools(mcp, devices_helper):
    @mcp.tool(
        description="Retrieve platform information for a specific device in Cisco NSO. Requires a 'device_name' parameter."
    )
    async def get_device_platform_tool(params: Dict[str, Any]):
        try:
            # validate required parameters
            if not params or "device_name" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: device_name"
                }
            
            # delegate to the service layer
            return await get_device_platform(devices_helper, params["device_name"])
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    @mcp.tool(
        description="Retrieve the available Network Element Driver (NED) IDs in Cisco NSO"
    )
    async def get_device_ned_ids_tool(params: Optional[Dict[str, Any]] = None):
        try:
            # delegate to the service layer
            return await get_device_ned_ids(devices_helper)
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

def main():
    # initialize FastMCP server
    mcp = FastMCP("nso-mcp", version="0.1.0", description="Cisco NSO MCP Server")
    
    # initialize NSO client
    client = NSORestconfClient(
        scheme="http",
        address="localhost",
        port=8080,
        timeout=10,
        username="admin",
        password="admin",
    )
    logger.info("NSORestconfClient initialized")

    # initialize NSO client helpers
    devices_helper = Devices(client)
    query_helper = Query(client)

    # register resources
    register_resources(mcp, query_helper)
    register_tools(mcp, devices_helper)

    # run the server
    logger.info("🚀 Starting Model Context Protocol (MCP) NSO Server with stdio connection")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
