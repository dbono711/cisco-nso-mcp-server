# Cisco NSO MCP Server

A Model Context Protocol (MCP) server implementation for Cisco NSO (Network Services Orchestrator) that enables AI-powered network automation through natural language interactions.

## Overview

This project integrates Cisco NSO with OpenAI's GPT models using the Model Context Protocol (MCP) framework, allowing network engineers to interact with network infrastructure using natural language. The implementation consists of two main components:

1. **MCP Server**: Provides network automation tools that can be called by AI models
2. **MCP Test Client**: Connects to the MCP server and integrates with OpenAI to enable conversational network management

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how AI models interact with external tools and services. MCP enables:

- **Tool Definition**: Structured way to define tools that AI models can use
- **Tool Discovery**: Mechanism for models to discover available tools
- **Tool Execution**: Standardized method for models to call tools and receive results
- **Context Management**: Efficient passing of context between tools and models

In this project, MCP acts as the bridge between OpenAI's GPT models and Cisco NSO, allowing the AI to query and interact with network devices through well-defined tool interfaces.

## How MCP Handles Requests from OpenAI

1. **Tool Registration**: The MCP server registers network automation tools with clear descriptions and parameter schemas
2. **Tool Discovery**: The client queries the MCP server for available tools and presents them to OpenAI
3. **Parameter Extraction**: OpenAI extracts parameters from user queries (e.g., device names) based on tool descriptions
4. **Tool Invocation**: The client receives tool calls from OpenAI and forwards them to the MCP server
5. **Result Processing**: The MCP server executes the requested operations against Cisco NSO and returns structured results
6. **Response Generation**: OpenAI uses the tool results to generate natural language responses

## Benefits of Using MCP

- **Separation of Concerns**: Clear separation between AI model capabilities and network automation logic
- **Standardized Interface**: Consistent way to define and call network automation tools
- **Enhanced Security**: The AI model never directly accesses network infrastructure
- **Extensibility**: Easy to add new network automation capabilities without changing the client or AI integration
- **Streaming Support**: Real-time streaming of responses for better user experience
- **Structured Data**: Well-defined schemas for tool inputs and outputs

## Current Tools

- `get_device_ned_ids`: Retrieves Network Element Driver (NED) IDs from Cisco NSO
- `get_device_platform`: Gets platform information for a specific device in Cisco NSO

## Requirements

- Python 3.13+
- Cisco NSO with RESTCONF API enabled
- OpenAI API key
- MCP library

## Setup

1. Clone the repository

2. Create a `secrets.env` file with your OpenAI API key:

   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

3. Ensure Cisco NSO is running and accessible via RESTCONF

## Usage

Start the MCP server:

```bash
python mcp-server.py
```

In another terminal, start the client:

```bash
python mcp-test-client.py mcp-server.py
```

You can then interact with your network infrastructure using natural language queries:

- "What NED IDs are available in NSO?"
- "Show me the platform information for device ios-0"

## Architecture

The system follows a client-server architecture:

1. **MCP Server (mcp-server.py)**:
   - Uses FastMCP framework to define network automation tools
   - Connects to Cisco NSO via RESTCONF
   - Provides asynchronous tool execution
   - Returns structured responses

2. **MCP Test Client (mcp-test-client.py)**:
   - Connects to the MCP server via stdio transport
   - Integrates with OpenAI's GPT-4o model
   - Handles tool calls and parameter formatting
   - Supports streaming responses
   - Provides a conversational interface

## Future Enhancements

- Additional NSO integration tools
- Support for device configuration changes
- Integration with Streamlit for web-based UI
- Enhanced error handling and validation
- Support for more complex network operations

## License

[MIT License](LICENSE)
