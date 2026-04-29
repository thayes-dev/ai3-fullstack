"""
branding.py -- Student-owned customization file.

Customize your app's appearance here. The instructor will NEVER modify this file.
Your changes survive all future git pulls.
"""
import streamlit as st

def apply_branding(config: dict) -> None:
    st.set_page_config(
        page_title=config.get("app_name"),
        page_icon="📊",
        layout="wide",
    )

    # Logo — full-width in sidebar
    st.sidebar.image(".streamlit/static/logo.png", use_container_width=True)

    # Custom CSS
    st.markdown("""
    <style>

    /* App background smoothing */
    .stApp {
        background-color: #0F1720;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0C141C;
        border-right: 1px solid #1F2A36;
    }

    /* Chat bubbles */
    .stChatMessage {
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
    }

    /* User message */
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #1A2430;
        border-left: 3px solid #3A7CA5;
    }

    /* Assistant message */
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #111A23;
        border-left: 3px solid #BFA37A;
    }

    /* Input box */
    textarea {
        background-color: #1A2430 !important;
        color: #E6EDF3 !important;
        border-radius: 8px !important;
    }

    /* Buttons */
    button {
        border-radius: 6px !important;
        border: 1px solid #2A3A4A !important;
    }

    /* Divider polish */
    hr {
        border-color: #1F2A36;
    }

    </style>
    """, unsafe_allow_html=True)