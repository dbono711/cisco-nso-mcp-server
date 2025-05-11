#!/usr/bin/env python3
"""
Cisco NSO MCP Server

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO via RESTCONF.
"""
import argparse
import os
from cisco_nso_restconf.client import NSORestconfClient
from cisco_nso_restconf.devices import Devices
from cisco_nso_restconf.query import Query
from mcp.server.fastmcp import FastMCP
from cisco_nso_mcp_server.services.environment import get_environment_summary
from cisco_nso_mcp_server.services.devices import get_device_platform, get_device_ned_ids
from typing import Optional, Dict, Any
from cisco_nso_mcp_server.utils import logger


def register_resources(mcp: FastMCP, query_helper: Query, devices_helper: Devices) -> None:
    """
    Register resources with the MCP server.
    
    This function registers all available resources with the MCP server,
    including the NSO environment summary resource that provides information
    about the network devices managed by NSO.
    
    Args:
        mcp: The FastMCP server instance to register resources with
        query_helper: The Query helper for interacting with NSO
        devices_helper: The Devices helper for interacting with NSO devices
    """
    @mcp.resource(
        uri="https://resources.cisco-nso-mcp.io/environment",
        description="NSO environment summary",
    )
    async def nso_environment() -> Dict[str, Any]:
        """
        This resource provides a summary of the NSO environment, including
        the number of devices managed by NSO, the distribution of operating
        systems, the number of device groups, and the distribution of device
        models.

        Returns:
            A dictionary containing summary information about the NSO
            environment.
        """
        try:
            # delegate to the service layer
            return await get_environment_summary(query_helper, devices_helper)
            
        except Exception as e:
            logger.error(f"Resource error: {str(e)}")

            return {
                "status": "error",
                "error_message": str(e)
            }

def register_tools(mcp: FastMCP, devices_helper: Devices) -> None:
    """    
    This function registers all available tools with the MCP server,
    including the get_device_platform tool that retrieves platform information
    for a specific device in Cisco NSO.
    
    Args:
        mcp: The FastMCP server instance to register tools with
        devices_helper: The Devices helper for interacting with NSO devices
    """
    @mcp.tool(
        description="Retrieve platform information for a specific device in Cisco NSO. Requires a 'device_name' parameter."
    )
    async def get_device_platform_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        This tool takes a single parameter, 'device_name', which is the name of
        the device for which to retrieve platform information. The response will
        include the platform name, platform version, and model information for
        the specified device.

        Args:
            params (Dict[str, Any]): A dictionary containing the 'device_name'
                parameter.

        Returns:
            A dictionary containing the platform information for the specified
            device.
        """
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
    async def get_device_ned_ids_tool(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        This tool retrieves the available Network Element Driver (NED) IDs in
        Cisco NSO. The response will include a list of available NED IDs.

        Args:
            params (Optional[Dict[str, Any]], optional): Unused parameter. Defaults to None.

        Returns:
            A dictionary containing a list of available NED IDs.
        """
        try:
            # delegate to the service layer
            return await get_device_ned_ids(devices_helper)
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Cisco NSO MCP Server")
    
    # NSO connection parameters
    nso_group = parser.add_argument_group('NSO Connection Options')
    nso_group.add_argument("--nso-scheme", default=os.environ.get("NSO_SCHEME", "http"),
                        help="NSO connection scheme (default: http)")
    nso_group.add_argument("--nso-address", default=os.environ.get("NSO_ADDRESS", "localhost"),
                        help="NSO server address (default: localhost)")
    nso_group.add_argument("--nso-port", type=int, default=int(os.environ.get("NSO_PORT", "8080")),
                        help="NSO server port (default: 8080)")
    nso_group.add_argument("--nso-timeout", type=int, default=int(os.environ.get("NSO_TIMEOUT", "10")),
                        help="NSO connection timeout in seconds (default: 10)")
    nso_group.add_argument("--nso-username", default=os.environ.get("NSO_USERNAME", "admin"),
                        help="NSO username (default: admin)")
    nso_group.add_argument("--nso-password", default=os.environ.get("NSO_PASSWORD", "admin"),
                        help="NSO password (default: admin)")
    
    # MCP server parameters
    mcp_group = parser.add_argument_group('MCP Server Options')
    mcp_group.add_argument("--transport", default=os.environ.get("MCP_TRANSPORT", "stdio"),
                        choices=["stdio", "sse"], help="MCP transport type (default: stdio)")
    
    # SSE-specific parameters
    sse_group = parser.add_argument_group('SSE Transport Options (only used when --transport=sse)')
    sse_group.add_argument("--host", default=os.environ.get("MCP_HOST", "0.0.0.0"),
                        help="Host to bind to when using SSE transport (default: 0.0.0.0)")
    sse_group.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", "8000")),
                        help="Port to bind to when using SSE transport (default: 8000)")
    
    args = parser.parse_args()
    
    # validate that host and port are provided if using SSE transport
    if args.transport == "sse" and (not args.host or not args.port):
        parser.error("--host and --port are required when using --transport=sse")
    
    return args

def main():
    """
    Main function to run the server.
    """

    # parse command line arguments
    args = parse_args()
    
    # initialize FastMCP server with configurable parameters
    mcp = FastMCP(
        "nso-mcp", 
        version="0.1.0", 
        description="Cisco NSO MCP Server",
        host=args.host if args.transport == "sse" else "0.0.0.0",
        port=args.port if args.transport == "sse" else 8000
    )
    
    # initialize NSO client with configurable parameters
    client = NSORestconfClient(
        scheme=args.nso_scheme,
        address=args.nso_address,
        port=args.nso_port,
        timeout=args.nso_timeout,
        username=args.nso_username,
        password=args.nso_password,
    )
    logger.info("NSORestconfClient initialized")

    # initialize NSO client helpers
    devices_helper = Devices(client)
    query_helper = Query(client)

    # register resources
    register_resources(mcp, query_helper, devices_helper)
    register_tools(mcp, devices_helper)

    # run the server with the specified transport
    if args.transport == "stdio":
        logger.info("🚀 Starting Model Context Protocol (MCP) NSO Server with stdio transport")
        mcp.run(transport='stdio')
    elif args.transport == "sse":
        logger.info(f"🚀 Starting Model Context Protocol (MCP) NSO Server with SSE transport on {args.host}:{args.port}")
        mcp.run(transport='sse')


if __name__ == "__main__":
    main()
