#!/usr/bin/env python3
"""
Cisco NSO MCP Server

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO via RESTCONF.
"""
import asyncio
import json
from requests.exceptions import HTTPError, RequestException
from cisco_nso_restconf.client import NSORestconfClient
from cisco_nso_restconf.devices import Devices
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional
from datetime import datetime
from loggerfactory import LoggerFactory

# initialize logger
logger = LoggerFactory.get_logger("mcp-server", "INFO")

# initialize FastMCP server
mcp = FastMCP("nso-mcp")

# initialize the NSORestconfClient
client = NSORestconfClient(
    scheme="http",
    address="localhost",
    port=8080,
    timeout=10,
    username="admin",
    password="admin",
)

logger.info("NSORestconfClient initialized")

# initialize the NSORestconfClient Devices helper class
devices_helper = Devices(client)

@mcp.tool(
    description="Retrieve the available Network Element Driver (NED) IDs in Cisco NSO"
)
async def get_device_ned_ids(params: Optional[Dict[str, Any]] = None):
    """
    Retrieve all Network Element Driver (NED) IDs configured in Cisco NSO.
    
    This tool queries the Cisco NSO RESTCONF API to get a list of all available
    Network Element Driver IDs, which represent the types of network devices
    that can be managed.
    
    Args:
        params: Optional parameters (not used for this tool)
        
    Returns:
        Dict: A structured response containing:
            - status: "success" or "error"
            - data: The NED IDs information if successful
            - metadata: Additional information about the response
            - error_message: Description of the error if status is "error"
    """
    try:
        # get device NED IDs using asyncio.to_thread since it's a bound method
        device_ned_ids = await asyncio.to_thread(devices_helper.get_device_ned_ids)
        formatted_response = {
            "status": "success",
            "data": {
                "device_ned_ids": device_ned_ids
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "count": len(device_ned_ids)
            }
        }
        logger.info(f"Formatted response: {json.dumps(formatted_response, indent=2)}")

        return formatted_response
            
    except (ValueError, HTTPError, RequestException) as e:
        # Handle HTTP and request-specific errors
        return {
            "device_ned_ids": [],
            "status": "error",
            "error_message": str(e)
        }

    except Exception as e:
        # Catch-all for unexpected errors
        return {
            "device_ned_ids": [],
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }

@mcp.tool(
    description="Retrieve platform information for a specific device in Cisco NSO. Requires a device_name parameter (e.g., 'ios-0', 'iosxr-1', 'nx-2')."
)
async def get_device_platform(params: Dict[str, Any]):
    """
    Retrieve platform information for a specific device in Cisco NSO.
    
    This tool queries the Cisco NSO RESTCONF API to get detailed platform
    information about a specific network device, including its type, model,
    and version.
    
    Args:
        params: A dictionary containing:
            - device_name: Name of the device to query (required)
        
    Returns:
        Dict: A structured response containing:
            - status: "success" or "error"
            - data: The device platform information if successful
            - metadata: Additional information about the response
            - error_message: Description of the error if status is "error"
    """
    try:
        # Validate required parameters
        if not params or "device_name" not in params:
            return {
                "status": "error",
                "error_message": "Missing required parameter: device_name"
            }
        
        device_name = params["device_name"]
        logger.info(f"Getting platform information for device: {device_name}")
        
        # Get device platform using asyncio.to_thread since it's a bound method
        device_platform = await asyncio.to_thread(
            devices_helper.get_device_platform, 
            device_name
        )
        formatted_response = {
            "status": "success",
            "data": {
                "device_platform": device_platform
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "device": device_name
            }
        }
        logger.info(f"Formatted response: {json.dumps(formatted_response, indent=2)}")

        return formatted_response
            
    except (ValueError, HTTPError, RequestException) as e:
        # Handle HTTP and request-specific errors
        error_msg = str(e)
        logger.error(f"HTTP/Request error for device {params.get('device_name', 'unknown')}: {error_msg}")
        return {
            "status": "error",
            "error_message": error_msg
        }
    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error for device {params.get('device_name', 'unknown')}: {error_msg}")
        return {
            "status": "error",
            "error_message": error_msg
        }

if __name__ == "__main__":
    # run the server using stdio transport for local process communication
    mcp.run(transport='stdio')
