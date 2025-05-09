import asyncio
from cisco_nso_mcp_server.utils import logger
from requests.exceptions import RequestException
from cisco_nso_restconf.devices import Devices
from typing import Dict, Any


async def get_device_platform(devices_helper: Devices, device_name: str) -> Dict[str, Any]:
    """
    Retrieve platform information for a specific device in Cisco NSO.
    """
    if not device_name:
        raise ValueError("Device name is required")
    
    try:
        # get device platform using asyncio.to_thread since it's a bound method
        device_platform = await asyncio.to_thread(
            devices_helper.get_device_platform, 
            device_name
        )
        response = device_platform
        logger.info(f"Successfully retrieved platform for device: {device_name}")

        return response
        
    except Exception as e:
        logger.error(f"Error retrieving platform for device {device_name}: {str(e)}")
        raise ValueError(f"Failed to retrieve platform for device {device_name}: {str(e)}")

async def get_device_ned_ids(devices_helper: Devices) -> Dict[str, Any]:
    """
    Retrieve the available Network Element Driver (NED) IDs in Cisco NSO.
    """
    try:
        # get device NED IDs using asyncio.to_thread since it's a bound method
        device_ned_ids = await asyncio.to_thread(devices_helper.get_device_ned_ids)
        response = device_ned_ids
        logger.info("Successfully retrieved NED IDs")

        return response
            
    except (ValueError, RequestException) as e:
        logger.error(f"Error retrieving NED IDs: {str(e)}")
        return {
            "device_ned_ids": [],
            "status": "error",
            "error_message": str(e)
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "device_ned_ids": [],
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }
