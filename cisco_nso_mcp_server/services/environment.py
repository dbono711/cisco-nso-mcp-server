"""
Cisco NSO MCP Server - Environment Service

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO via RESTCONF.
"""
import asyncio
from cisco_nso_mcp_server.utils import logger
from cisco_nso_restconf.query import Query
from cisco_nso_restconf.devices import Devices
from typing import Dict, Any, List


def _process_device_data(device_platforms: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Process raw device platform data into a structured dictionary.
    """

    # build device dictionary
    devices = {}
    for device_entry in device_platforms:
        device_info = {}
        device_name = None
    
        # extract all label-value pairs for this device
        for item in device_entry['select']:
            label = item['label']
            value = item['value']
        
            # store the device name to use as the key
            if label == 'name':
                device_name = value
            else:
                device_info[label] = value
    
        # add the device to our dictionary if we found a name
        if device_name:
            devices[device_name] = device_info

    return devices

def _generate_insights(devices: Dict[str, Dict[str, Any]], device_groups: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate insights from the device data.
    """

    # generate insights from the device data
    insights = {}
        
    # count total devices
    insights["device_count"] = len(devices)
        
    # count unique operating systems
    os_types = {}
    for device, info in devices.items():
        os_type = info.get("os", "unknown").lower()
        os_types[os_type] = os_types.get(os_type, 0) + 1
        
    insights["os_distribution"] = os_types
    insights["unique_os_count"] = len(os_types)
        
    # count unique versions per OS
    os_versions = {}
    for device, info in devices.items():
        os_type = info.get("os", "unknown").lower()
        version = info.get("version", "unknown")
            
        if os_type not in os_versions:
            os_versions[os_type] = {}
            
        os_versions[os_type][version] = os_versions[os_type].get(version, 0) + 1
        
    insights["os_versions"] = os_versions
        
    # count unique device models
    models = {}
    for device, info in devices.items():
        model = info.get("model", "unknown")
        models[model] = models.get(model, 0) + 1
        
    insights["model_distribution"] = models
    insights["unique_model_count"] = len(models)
        
    # count device series insights (based on naming patterns)
    series_counts = {}
    for device in devices:
        # extract series from device name (e.g., ios, iosxr, nxos)
        parts = device.split('-')
        if len(parts) > 0:
            series = parts[0]
            series_counts[series] = series_counts.get(series, 0) + 1
        
    insights["series_distribution"] = series_counts

    # process device groups data
    if device_groups and "tailf-ncs:device-group" in device_groups:
        processed_groups = []
        
        for group in device_groups["tailf-ncs:device-group"]:
            # Create a simplified group object with only the required fields
            processed_group = {
                "name": group.get("name", ""),
                "member": group.get("member", []),
                "ned-id": group.get("ned-id", [])
            }
            processed_groups.append(processed_group)
            
        insights["device_groups"] = processed_groups
        insights["device_group_count"] = len(processed_groups)
    else:
        insights["device_groups"] = []
        insights["device_group_count"] = 0
    
    return insights

async def get_environment_summary(query_helper: Query, devices_helper: Devices) -> Dict[str, Any]:
    """
    Retrieve a summary of the NSO environment.
    
    This function fetches device platform data and device groups from NSO,
    processes the raw data into a structured format, and generates insights
    about the environment including device counts, operating system distribution,
    model distribution, and device group information.
    
    Args:
        query_helper (Query): The Query helper for interacting with NSO.
        devices_helper (Devices): The Devices helper for interacting with NSO devices.
    
    Returns:
        Dict[str, Any]: A dictionary containing summary information about the NSO
                        environment, including device counts, OS distribution,
                        model distribution, and device group details.
    
    Raises:
        ValueError: If there is an error retrieving or processing the environment data.
    """
    try:
        logger.info("Retrieving environment data from NSO")
        
        # query device platforms
        device_platforms = await asyncio.to_thread(query_helper.query_device_platform)
        
        # query device groups
        device_groups = await asyncio.to_thread(devices_helper.get_device_groups)
        
        # process raw device platform data into structured format
        devices = _process_device_data(device_platforms)
        
        # generate insights from device data
        insights = _generate_insights(devices, device_groups)
        logger.info("Successfully generated environment summary")

        return insights
        
    except Exception as e:
        logger.error(f"Error retrieving environment data: {str(e)}")
        raise ValueError(f"Failed to retrieve NSO environment: {str(e)}")
