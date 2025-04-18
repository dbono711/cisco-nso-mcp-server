#!/usr/bin/env python3
import streamlit as st
import asyncio
import os
import json
import threading
from contextlib import AsyncExitStack
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from loggerfactory import LoggerFactory
import time


class MCPSessionManager:
    def __init__(self, server_script_path):
        self.server_script_path = server_script_path
        self.logger = LoggerFactory.get_logger("network-chatops-assistant", "INFO")
        self.loop = asyncio.new_event_loop()
        self.tools = []
        self.session = None
        self.exit_stack = None
        self._initialize()
    
    def _initialize(self):
        self.logger.info("Initializing MCP session...")
        
        # run the initialization in a separate thread to avoid blocking Streamlit
        thread = threading.Thread(target=self._setup_session)
        thread.daemon = True
        thread.start()
    
    def _setup_session(self):
        asyncio.set_event_loop(self.loop)
        
        async def setup():
            self.exit_stack = AsyncExitStack()
            server_params = StdioServerParameters(
                command="python",
                args=[self.server_script_path],
                env=None
            )
            
            try:
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                stdio, write = stdio_transport
                self.session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
                await self.session.initialize()
                
                # list available tools
                response = await self.session.list_tools()
                self.tools = response.tools
                self.logger.info(f"Connected to server with tools: {', '.join([tool.name for tool in self.tools])}")
            
            except Exception as e:
                self.logger.error(f"Error connecting to MCP server: {e}")
                if self.exit_stack:
                    await self.exit_stack.aclose()
        
        self.loop.run_until_complete(setup())
    
    def call_tool(self, tool_name, params=None):        
        async def _call():
            try:
                self.logger.info(f"Calling tool '{tool_name}' with params: {params}")
                response = await self.session.call_tool(tool_name, params)
                self.logger.info(f"Tool '{tool_name}' response: {response}")
                
                return response

            except Exception as e:
                self.logger.error(f"Error calling tool {tool_name}: {e}")

                return {"error": str(e)}
        
        return self.loop.run_until_complete(_call())
    
    def get_tools(self):
        return self.tools


# create a singleton for MCP session manager
@st.cache_resource
def get_mcp_manager(server_script_path):
    return MCPSessionManager(server_script_path)


class Application:
    def __init__(self):
        load_dotenv("secrets.env")  # load environment variables
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.logger = LoggerFactory.get_logger("network-chatops-assistant", "INFO")

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

    def render_chat(self):
        
        # get tools
        tools = self.mcp_manager.get_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in tools
        ]

        # create a container for the chat messages
        chat_container = st.container()
        
        # create the input field at the bottom
        prompt = st.chat_input("Ask me about your NSO instance...")
        
        # display messages in the container
        with chat_container:
            for message in st.session_state.messages:
                # Only display user and assistant content messages, not system, tool, or tool_calls messages
                if (message["role"] != "system" and 
                    message["role"] != "tool" and 
                    "tool_calls" not in message and
                    "content" in message):
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        
        # handle user input
        if prompt:
            # add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # display user message
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                # show assistant response
                with st.chat_message("assistant"):
                    response_container = st.empty()
                    
                    # Function to handle streaming responses
                    def handle_streaming_response(response_stream):
                        full_response = ""
                        # Display the streaming response
                        for chunk in response_stream:
                            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                                content_chunk = chunk.choices[0].delta.content
                                full_response += content_chunk
                                response_container.markdown(full_response)
                        return full_response

                    # Check if we need to call tools or can directly stream a response
                    # First make a non-streaming call to check for tool calls
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=st.session_state.messages,
                        tools=available_tools
                    )

                    # check if the response has content
                    message = response.choices[0].message
                    has_content = hasattr(message, 'content') and message.content is not None
                    has_tool_calls = hasattr(message, 'tool_calls') and message.tool_calls

                    if not has_content and has_tool_calls:
                        # handle tool calls directly
                        for tool_call in message.tool_calls:
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
                            
                            # use the MCP manager to call the tool
                            result = self.mcp_manager.call_tool(tool_name, tool_args)
                            
                            # add the result to the messages
                            st.session_state.messages.append({
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
                            st.session_state.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(result)
                            })
                        
                        # get a final response from OpenAI with the tool results - use streaming
                        stream_response = self.openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=st.session_state.messages,
                            stream=True
                        )
                        
                        # Handle the streaming response
                        final_content = handle_streaming_response(stream_response)
                        
                        # add the final response to the conversation history
                        if final_content:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": final_content
                            })
                        else:
                            # handle case where final response has no content
                            error_message = "No response content received from the model."
                            response_container.error(error_message)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_message
                            })
                    elif has_content:
                        # first add the initial content we already received
                        initial_content = message.content
                        response_container.markdown(initial_content)
                        
                        # add to conversation history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": initial_content
                        })
                    else:
                        # handle case where response has neither content nor tool calls
                        error_message = "Received an empty response from the model."
                        response_container.error(error_message)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_message
                        })
            
            # rerun to update the UI with the new messages
            st.rerun()
    
    def configure(self):
        
        # initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "assistant",
                    "content": "Welcome to the Cisco NSO Network Assistant! I can help you retrieve information from your NSO instance. How can I help you today?",
                }
            ]
        
        # sidebar
        st.sidebar.header("Available tools")
        tools = self.mcp_manager.get_tools()
        
        # check if tools are available yet
        if not tools:
            st.sidebar.info("Loading tools, please wait...")
            time.sleep(0.5) # small delay to avoid too frequent reruns
            st.rerun()
        else:
            # display available tools
            for tool in tools:
                st.sidebar.expander(f"{tool.name}").write(f"{tool.description}")
        
        st.sidebar.write(st.session_state.messages)
        
        # create tabs
        chat, logs = st.tabs(["Chat", "Logs"])

        with chat:
            self.render_chat()

    def main(self):
        st.set_page_config(
            layout="wide",
            page_title="NSO Chat Assistant",
            page_icon=":robot_face:"
        )
        st.title("NSO Chat Assistant")
        st.caption(":robot_face: A ChatOps assistant powered by OpenAI and Cisco NSO, enabled by MCP")
        st.write(
            """
            Your AI-powered assistant for answering questions about your NSO instance.
            Ask questions about devices, configurations, and more using natural language.
            Get instant insights from the NSO database through intuitive conversations.
            """
        )
        
        # initialize MCP manager
        self.mcp_manager = get_mcp_manager("mcp_server.py")
        
        # configure the UI
        self.configure()


if __name__ == '__main__':
    Application().main()
