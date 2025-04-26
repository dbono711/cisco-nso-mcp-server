# Cisco NSO MCP Server

A Model Context Protocol (MCP) server implementation for Cisco NSO (Network Services Orchestrator) that enables AI-powered network automation through natural language interactions.

## Overview

This package provides a standalone MCP server for Cisco NSO, written in Python, that can be installed with ```pip``` and run as a command-line tool. It exposes capabilities in Cisco NSO as MCP tools and resources that can be consumed by any MCP-compatible client.

```bash
# Install the package
pip install cisco-nso-mcp-server

# Run the server
cisco-nso-mcp-server
```

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that standardizes how AI models interact with external tools and services. MCP enables:

- **Tool Definition**: Structured way to define tools that AI models can use
- **Tool Discovery**: Mechanism for models to discover available tools
- **Tool Execution**: Standardized method for models to call tools and receive results
- **Context Management**: Efficient passing of context between tools and models
- **Framework Agnostic**: Works across multiple AI frameworks including OpenAI, Anthropic, Google Gemini, and others
- **Interoperability**: Provides a common language for AI systems to communicate with external tools

### Note on MCP Flexibility

Although the primary use case for MCP is integration with LLMs, MCP and similar tool frameworks (like Smithery) are LLM-agnostic - they're simply APIs with a specific protocol. This means you can:

- **Use them directly** in any application without an LLM
- **Let an LLM control them** through an integration layer
- **Mix both approaches** depending on your specific needs and use cases

This flexibility makes MCP tools valuable beyond just LLM applications, serving as standardized interfaces for various automation needs.

## Features

- **Stdio Transport**: By default, the server uses stdio transport for process-bound communication
- **SSE Transport**: Optionally, the server can use SSE transport for web-bound communication
- **Tool-First Design**: Network operations are defined as discrete tools with clear interfaces
- **Asynchronous Processing**: All network operations are implemented asynchronously for better performance
- **Structured Responses**: Consistent response format with status, data, and metadata sections
- **Environment Resources**: Provides contextual information about the NSO environment

## Available Tools and Resources

### Tools

- `get_device_ned_ids_tool`: Retrieves Network Element Driver (NED) IDs from Cisco NSO
- `get_device_platform_tool`: Gets platform information for a specific device in Cisco NSO

### Resources

- `https://cisco-nso-mcp.resources/environment`: Provides a comprehensive summary of the NSO environment:
  - Device count
  - Operating System Distribution
  - Unique Operating System Count
  - Unique Model Count
  - Model Distribution
  - Device Series Distribution


## Requirements

- Python 3.13+
- Cisco NSO with RESTCONF API enabled
- Network connectivity to NSO RESTCONF API

## Installation

```bash
# Install from PyPI
pip install cisco-nso-mcp-server

# Verify installation
which cisco-nso-mcp-server
```

## Usage

### Running the Server

```bash
# Run with default NSO connection and MCP settings (see Configuration Options below for details)
cisco-nso-mcp-server

# Run with custom NSO connection parameters
cisco-nso-mcp-server --nso-address 192.168.1.100 --nso-port 8888 --nso-username myuser --nso-password mypass
```

### Configuration Options

You can configure the server using command-line arguments or environment variables:

#### NSO Connection Parameters

| Command-line Argument | Environment Variable | Default | Description |
|----------------------|---------------------|---------|-------------|
| `--nso-scheme`       | `NSO_SCHEME`        | http    | NSO connection scheme (http/https) |
| `--nso-address`      | `NSO_ADDRESS`       | localhost | NSO server address |
| `--nso-port`         | `NSO_PORT`          | 8080    | NSO server port |
| `--nso-timeout`      | `NSO_TIMEOUT`       | 10      | Connection timeout in seconds |
| `--nso-username`     | `NSO_USERNAME`      | admin   | NSO username |
| `--nso-password`     | `NSO_PASSWORD`      | admin   | NSO password |

#### MCP Server Parameters

| Command-line Argument | Environment Variable | Default | Description |
|----------------------|---------------------|---------|-------------|
| `--transport`        | `MCP_TRANSPORT`     | stdio   | MCP transport type (stdio/sse) |

#### SSE Transport Options (only used when --transport=sse)

| Command-line Argument | Environment Variable | Default | Description |
|----------------------|---------------------|---------|-------------|
| `--host`             | `MCP_HOST`          | 0.0.0.0 | Host to bind to when using SSE transport |
| `--port`             | `MCP_PORT`          | 8000    | Port to bind to when using SSE transport |

Environment variables take precedence over default values but are overridden by command-line arguments.

### Connecting to the Server

#### Stdio Transport

For stdio transport, you'll need to spawn the server process and communicate through stdin/stdout:

```python
from mcp import ClientSession, StdioServerParameters
from contextlib import AsyncExitStack

async def connect():
    exit_stack = AsyncExitStack()
    server_params = StdioServerParameters(
        command="cisco-nso-mcp-server",
        args=[],
        env=None
    )
    
    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()
    
    # Now you can use the session to call tools and read resources
    return session
```

#### SSE Transport

For SSE transport, you can connect to the server using a standard HTTP client:

```python
from mcp import ClientSession, SSEServerParameters
from contextlib import AsyncExitStack

async def connect():
    exit_stack = AsyncExitStack()
    server_params = SSEServerParameters(
        url="http://localhost:8000",
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    
    sse_transport = await exit_stack.enter_async_context(sse_client(server_params))
    session = await exit_stack.enter_async_context(ClientSession(sse_transport))
    await session.initialize()
    
    # Now you can use the session to call tools and read resources
    return session
```

## Asynchronous Implementation Details

The MCP server leverages Python's asynchronous programming capabilities to efficiently handle network operations:

- **Async Function Definitions**: All tool functions are defined with `async def` to make them coroutines
- **Non-blocking I/O**: Network calls to Cisco NSO are wrapped with `asyncio.to_thread()` to prevent blocking the event loop
- **Concurrent Processing**: Multiple tool calls can be processed simultaneously without waiting for previous operations to complete
- **Error Handling**: Asynchronous try/except blocks capture and properly format errors from network operations

## License

[MIT License](LICENSE)
