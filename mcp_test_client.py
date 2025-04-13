#!/usr/bin/env python3
import asyncio
import os
import json
from typing import Optional
from contextlib import AsyncExitStack
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from loggerfactory import LoggerFactory


class MCPClient:
    def __init__(self):
        load_dotenv("secrets.env")  # load environment variables from secrets.env
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.logger = LoggerFactory.get_logger("mcp-client", "INFO")
        
        # system prompt for the assistant
        self.system_prompt = """
        You are a network automation assistant specializing in network infrastructure management. 
        You have access to tools that can interact directly with network devices and Cisco NSO (Network Services Orchestrator).

        AVAILABLE TOOLS:
        1. get_device_ned_ids - Retrieves the Network Element Driver (NED) IDs from Cisco NSO
           - This tool takes no parameters
        2. get_device_platform - Retrieves platform information for a specific device
           - Required parameter: device_name (e.g., 'ios-0', 'iosxr-1', 'nx-2')
           - Example usage: When asked about a device's platform, extract the device name and call this tool

        GUIDELINES FOR TOOL USAGE:
        - When a user asks about NED IDs, use the get_device_ned_ids tool
        - When a user asks about a specific device's platform, extract the device name from their query and use get_device_platform with the device_name parameter
        - Always extract device names from user queries when they mention specific devices

        Provide clear, accurate, and technical responses about network configurations, device status, and automation capabilities.
        """

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        self.logger.info(f"Connected to server with tools: {', '.join([tool.name for tool in tools])}")

    async def process_query(self, query: str) -> str:
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in response.tools
        ]

        # initial OpenAI API call
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=available_tools
        )

        # process response and handle tool calls
        final_text = []

        # check if the response has content
        if not hasattr(response.choices[0].message, 'content') or response.choices[0].message.content is None:
            # handle tool calls directly
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    
                    # parse the arguments string to a Python dict
                    try:
                        # make sure we have a proper JSON object
                        if tool_call.function.arguments.strip() == "":
                            tool_args = {}
                        else:
                            tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # wrap the args in a params object
                    tool_args = {"params": tool_args}
                    
                    # execute tool call with properly formatted arguments
                    self.logger.info(f"Calling tool '{tool_name}' with args '{tool_call.function.arguments}'")
                    result = await self.session.call_tool(tool_name, tool_args)
                    
                    # add the assistant's tool call to the conversation
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_args)
                                }
                            }
                        ]
                    })
                    
                    # add the tool result to the conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content
                    })
                
                # get next response from OpenAI
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    stream=True
                )
                
                # handle streaming response
                streaming_content = []
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        streaming_content.append(content_piece)
                        print(content_piece, end="", flush=True) # print each chunk as it arrives
                
                # combine all chunks into the final response
                if streaming_content:
                    final_text.append("".join(streaming_content))
                else:
                    # if no streaming content was received, log it
                    self.logger.warning("No streaming content received")
                    
                # Return empty string since we've already printed the response
                return ""
        else:
            # handle regular text response with streaming
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True
            )
            
            # handle streaming response
            streaming_content = []
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content_piece = chunk.choices[0].delta.content
                    streaming_content.append(content_piece)
                    print(content_piece, end="", flush=True) # print each chunk as it arrives

            # combine all chunks into the final response
            if streaming_content:
                final_text.append("".join(streaming_content))
            else:
                # if no streaming content was received, log it
                self.logger.warning("No streaming content received")
                
            # return empty string since we've already printed the response
            return ""

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
        self.logger.info("Client resources cleaned up")
    
async def main():
    """
    Main function to run the client
    """
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
