# -*- mode: python; python-indent: 4 -*-
import dotenv
import streamlit as st
from openai_client import OpenAi


class Application(OpenAi):
    """Docstring missing."""

    def __init__(self):
        """Docstring missing."""
        OpenAi.__init__(self)
        dotenv.load_dotenv("secrets.env")  # Load environment variables


    def configure_streamlit(self):
        st.set_page_config(
            layout="wide",
            page_title="Network Chat Assistant",
            page_icon=":robot_face:"
        )
        st.title("Network Chat Assistant")
        st.caption(":robot_face: A Network chat assistant powered by OpenAI")
        st.write(
            """
            Your AI-powered assistant for answering questions about network devices and configurations.
            Ask questions about devices, configurations, and more using natural language.
            Get instant insights from the **NSO** database through intuitive conversations.
            """
        )

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "How may I assist you in answering questions about network devices and configurations?",
                }
            ]
        
        # Create tabs
        chat, logs, features = st.tabs(["Chat", "Logs", "Features"])


    def main(self):
        """Docstring missing."""
        self.configure_streamlit()


if __name__ == '__main__':
    Application().main()