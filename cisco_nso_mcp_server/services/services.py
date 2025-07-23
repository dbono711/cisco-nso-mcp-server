"""
Cisco NSO MCP Server - Services Service

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO services via RESTCONF.
"""
import asyncio
from cisco_nso_mcp_server.utils import logger
from requests.exceptions import RequestException
from cisco_nso_restconf.client import NSORestconfClient
from typing import Dict, Any


async def get_service_types(client: NSORestconfClient) -> Dict[str, Any]:
    """
    Retrieve the service types for services in Cisco NSO.

    Args:
        client (NSORestconfClient): The NSORestconfClient for interacting with NSO.

    Returns:
        Dict[str, Any]: A dictionary containing the service types for services in Cisco NSO.

    Raises:
        ValueError: If the service types cannot be retrieved.
    """
    try:
        # get service types using asyncio.to_thread since it's a bound method
        resource = "tailf-ncs:services/service-type"
        service_types = await asyncio.to_thread(client.get, resource)
        response = service_types.json()
        logger.info("Successfully retrieved service types")

        return response
            
    except (ValueError, RequestException) as e:
        logger.error(f"Error retrieving service types: {str(e)}")
        return {
            "service_types": [],
            "status": "error",
            "error_message": str(e)
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "service_types": [],
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }

async def get_services(client: NSORestconfClient, service_type: str) -> Dict[str, Any]:
    """
    Retrieve services in Cisco NSO.

    Args:
        client (NSORestconfClient): The NSORestconfClient for interacting with NSO.

    Returns:
        Dict[str, Any]: A dictionary containing the services in Cisco NSO.

    Raises:
        ValueError: If the services cannot be retrieved.
    """
    try:
        # get services using asyncio.to_thread since it's a bound method
        resource = f"tailf-ncs:services/{service_type}:{service_type}"
        services = await asyncio.to_thread(client.get, resource)
        response = services.json()
        logger.info("Successfully retrieved services")

        return response
            
    except (ValueError, RequestException) as e:
        logger.error(f"Error retrieving services: {str(e)}")
        return {
            "services": [],
            "status": "error",
            "error_message": str(e)
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "services": [],
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }
