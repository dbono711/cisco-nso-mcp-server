#!/usr/bin/env python3
import os
import dotenv
import streamlit as st
from openai import OpenAI

dotenv.load_dotenv("secrets.env")


class OpenAi:
    """Docstring missing."""

    def __init__(self) -> None:
        """Docstring missing."""

        # initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_response(self, content):
        """Docstring missing."""
        completion = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a network automation assistant specializing in network infrastructure management. You have access to tools that can interact directly with network devices and Cisco NSO (Network Services Orchestrator). Provide clear, accurate, and technical responses about network configurations, device status, and automation capabilities. When appropriate, use the available MCP tools to retrieve real-time information from the network environment.",
                },
                {
                    "role": "user",
                    "content": content
                },
            ],
        )

        response = completion.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": response})

        return response
