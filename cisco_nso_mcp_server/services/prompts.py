"""
Cisco NSO MCP Server - Prompts Service

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO via RESTCONF.
"""
from fastmcp import Context
from fastmcp.prompts.prompt import Message, PromptMessage
from cisco_nso_mcp_server.utils import logger


async def get_default_nso_prompt_summary(ctx: Context) -> PromptMessage:
    """
    Retrieve a default prompt for NSO.
    """
    try:
        logger.info("Retrieving default prompt for NSO")
        environment_data = await ctx.read_resource("https://resources.cisco-nso-mcp.io/environment")
        

        return Message(role="user", content=f"""
        You are a network automation assistant specializing in network infrastructure management. 
        You have access to tools that can interact directly with Cisco NSO (Network Services Orchestrator).

        NSO Environment Information:
        {environment_data[0].content if environment_data else "Unable to retrieve environment data"}


        GUIDELINES FOR TOOL USAGE:
        - Always extract device names as 'device_name' from user queries when they mention needing information about a specific device
        - If the user asks for a device's configuration, or any aspect of configuration on a device such as interfaces, use the get_device_config_tool

        Provide clear, accurate, and technical responses about network configurations, device status, and automation capabilities.
        """)

    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}")
        raise ValueError(f"Failed to generate prompt: {str(e)}")
