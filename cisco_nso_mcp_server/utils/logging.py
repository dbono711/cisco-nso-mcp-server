"""
Simplified logging interface for the Cisco NSO MCP Server.

This module provides a pre-configured logger that can be imported directly:
    from utils.logging import logger
"""
# import and expose the default logger from LoggerFactory
from cisco_nso_mcp_server.utils.loggerfactory import default_logger as logger

# you can also expose the LoggerFactory if needed for advanced use cases
from cisco_nso_mcp_server.utils.loggerfactory import LoggerFactory

__all__ = ["logger", "LoggerFactory"]