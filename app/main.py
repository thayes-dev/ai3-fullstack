"""
Northbrook Q&A -- Streamlit Chat Application

Session 2.1: Build a stateful chat application with RAG integration.

This is your starter template. The structure is complete. Your job:
  1. Initialize session state for messages, conversations, and current chat (Step 1)
  2. Implement the chat input handler (Step 5)

Steps 2 (sidebar), 3 (display), and 4 (source display) are provided.
The RAG pipeline is handled by app/rag.py (instructor-managed).

Run with: streamlit run app/main.py
"""

import sys
from pathlib import Path

# Streamlit adds the script's directory (app/) to sys.path, not the project
# root. This fix ensures package imports like `from app.branding` resolve
# correctly regardless of where `streamlit run` is invoked from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
import yaml
from app.branding import apply_branding
from app.rag import get_response

# ============================================================
# LOAD CONFIG & APPLY BRANDING
# ============================================================
with open(_PROJECT_ROOT / "student_config.yaml") as f:
    config = yaml.safe_load(f)

apply_branding(config)

# ============================================================
# STEP 1: Initialize Session State
# ============================================================
# TODO: Initialize three session state keys using the guard pattern:
#
#   "messages"      -> empty list []
#                      (current conversation's message history)
#
#   "conversations" -> empty dict {}
#                      (all conversations, keyed by chat_id)
#
#   "current_chat"  -> None
#                      (ID of the active conversation)
#
# Use: if "key" not in st.session_state:
#          st.session_state.key = value
#
# Then: auto-create the first conversation if current_chat is None:
#   if st.session_state.current_chat is None:
#       chat_id = "chat_0"
#       st.session_state.current_chat = chat_id
#       st.session_state.conversations[chat_id] = []
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# Auto-create first conversation if none exists
if st.session_state.current_chat is None:
    chat_id = "chat_0"
    st.session_state.current_chat = chat_id
    st.session_state.conversations[chat_id] = []

# ============================================================
# STEP 2: Sidebar — Chat History (PROVIDED — do not modify)
# ============================================================
# Safety net: ensure session state keys exist even if Step 1 is not yet
# implemented. Once you complete Step 1, these lines are redundant.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "chat_0"
    st.session_state.conversations["chat_0"] = []

with st.sidebar:
    st.title(config.get("app_name", "Northbrook Q&A"))
    st.caption(config.get("tagline", "Ask questions about Northbrook Partners"))

    if st.button("+ New Chat", use_container_width=True):
        chat_id = f"chat_{len(st.session_state.conversations)}"
        st.session_state.current_chat = chat_id
        st.session_state.messages = []
        st.session_state.conversations[chat_id] = []
        st.rerun()

    st.divider()

    for chat_id, msgs in st.session_state.conversations.items():
        if msgs:
            label = next(
                (m["content"][:30] + "..." for m in msgs if m["role"] == "user"),
                "New Chat",
            )
        else:
            label = "Empty Chat"

        if st.button(label, key=chat_id, use_container_width=True):
            # Save current conversation before switching
            if st.session_state.current_chat:
                st.session_state.conversations[st.session_state.current_chat] = (
                    st.session_state.messages.copy()
                )
            st.session_state.current_chat = chat_id
            st.session_state.messages = msgs.copy()
            st.rerun()

    st.divider()
    msg_count = len(st.session_state.get("messages", []))
    st.write(f"Messages: {msg_count}")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        if st.session_state.current_chat:
            st.session_state.conversations[st.session_state.current_chat] = []
        st.rerun()


# ============================================================
# STEP 3: Display Chat History (PROVIDED — do not modify)
# ============================================================
# Show welcome message if no messages yet
if not st.session_state.get("messages"):
    welcome = config.get(
        "welcome_message",
        "Hello! Ask me anything about Northbrook Partners.",
    )
    with st.chat_message("assistant"):
        st.markdown(welcome)

# Display all previous messages
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# STEP 4: Source Display Helper (PROVIDED — do not modify)
# ============================================================
def display_sources(sources: list[dict]):
    """Show retrieved sources in a collapsible expander."""
    if sources:
        with st.expander(f"Sources ({len(sources)})"):
            for i, src in enumerate(sources, 1):
                name = src["metadata"].get("source", "Unknown")
                score = src.get("score", 0.0)
                st.markdown(f"**{i}. {name}** (relevance: {score:.2f})")
                st.caption(src["text"][:200] + "...")
    else:
        st.caption("No sources — answering from general knowledge.")


# ============================================================
# STEP 5: Chat Input Handler
# ============================================================
# TODO: Implement the chat input handler
#
# Use: if prompt := st.chat_input("Ask a question..."):
#
# Inside the block:
#   a. Append the user message to st.session_state.messages
#      Format: {"role": "user", "content": prompt}
#   b. Display the user message with:
#      with st.chat_message("user"):
#          st.markdown(prompt)
#   c. Call get_response(prompt, st.session_state.messages) to get a response
#      response.answer = the text reply
#      response.sources = list of source dicts (may be empty)
#   d. Display the assistant message with:
#      with st.chat_message("assistant"):
#          st.markdown(response.answer)
#          display_sources(response.sources)
#   e. Append the assistant message to st.session_state.messages
#      Format: {"role": "assistant", "content": response.answer}
#   f. Save the conversation:
#      st.session_state.conversations[st.session_state.current_chat] = (
#          st.session_state.messages.copy()
#      )
# ============================================================
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = get_response(prompt, st.session_state.messages)

    with st.chat_message("assistant"):
        st.markdown(response.answer)
        display_sources(response.sources)

    st.session_state.messages.append({"role": "assistant", "content": response.answer})
    st.session_state.conversations[st.session_state.current_chat] = (
        st.session_state.messages.copy()
    )
