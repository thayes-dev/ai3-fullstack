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

# pysqlite3 shim — required for ChromaDB on Streamlit Community Cloud.
# Community Cloud's system sqlite3 is older than ChromaDB requires.
# pysqlite3-binary ships a newer sqlite3; we swap it in before chromadb imports.
# Local Mac dev skips this gracefully (pysqlite3 not installed).
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import uuid

import streamlit as st
import yaml
from dotenv import load_dotenv

from app.branding import apply_branding
from app.feedback import get_feedback_summary, submit_feedback
from app.rag import get_response

load_dotenv(_PROJECT_ROOT / ".env")

# ==============================================================
# === DEPLOYMENT: API KEYS ===
# Per-visitor key entry. No keys baked into the deployed app —
# anyone with the URL would burn the owner's credits.
# Keys live in os.environ for this session only — lost on refresh.
# ==============================================================
with st.sidebar:
    st.subheader("API Keys")
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Get one at console.anthropic.com",
    )
    voyage_key = st.text_input(
        "Voyage API Key",
        type="password",
        value=os.getenv("VOYAGE_API_KEY", ""),
        help="Get one at voyageai.com",
    )

if not anthropic_key or not voyage_key:
    st.warning("Enter both API keys in the sidebar to start chatting.")
    st.stop()

os.environ["ANTHROPIC_API_KEY"] = anthropic_key
os.environ["VOYAGE_API_KEY"] = voyage_key
# === END DEPLOYMENT ===

# ============================================================
# LOAD CONFIG & APPLY BRANDING
# ============================================================
with open(_PROJECT_ROOT / "student_config.yaml") as f:
    config = yaml.safe_load(f)

apply_branding(config)

# Initialize Phoenix tracing ONCE per session
if "phoenix_initialized" not in st.session_state:
    try:
        from phoenix.otel import register
        register(
            project_name=os.getenv("PHOENIX_PROJECT_NAME", "ai3"),
            auto_instrument=True,
        )
    except Exception:
        pass
    st.session_state.phoenix_initialized = True

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ============================================================
# STEP 1: Initialize Session State
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if st.session_state.current_chat is None:
    chat_id = "chat_0"
    st.session_state.current_chat = chat_id
    st.session_state.conversations[chat_id] = []
# ============================================================


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

    summary = get_feedback_summary()
    if summary["total"] > 0:
        st.write(
            f"Feedback: {summary['positive']} :thumbsup: / "
            f"{summary['negative']} :thumbsdown:"
        )

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

# Feedback callbacks
def _save_feedback(index):
    feedback_value = st.session_state[f"fb_{index}"]
    st.session_state.messages[index]["feedback"] = feedback_value
    span_id = st.session_state.messages[index].get("span_id", "")
    if span_id:
        submit_feedback(span_id, feedback_value)
    st.session_state.conversations[st.session_state.current_chat] = (
        st.session_state.messages.copy()
    )
    st.toast("Thanks for the positive feedback!" if feedback_value == 1
             else "Thanks — you can add details below.")


def _save_feedback_note(index):
    note = st.session_state.get(f"note_{index}", "")
    if not note:
        return
    span_id = st.session_state.messages[index].get("span_id", "")
    if span_id:
        submit_feedback(span_id, 0, note=note)
    st.session_state.messages[index]["feedback_note"] = note
    st.session_state.conversations[st.session_state.current_chat] = (
        st.session_state.messages.copy()
    )
    st.toast("Detailed feedback submitted!")


def render_feedback(index):
    message     = st.session_state.messages[index]
    existing_fb = message.get("feedback", None)
    st.session_state[f"fb_{index}"] = existing_fb
    st.feedback(
        "thumbs",
        key=f"fb_{index}",
        disabled=existing_fb is not None,
        on_change=_save_feedback,
        args=[index],
    )
    if existing_fb == 0 and not message.get("feedback_note"):
        st.text_input(
            "What went wrong?",
            key=f"note_{index}",
            placeholder="Help us improve (press Enter to submit)",
            on_change=_save_feedback_note,
            args=[index],
        )
    elif message.get("feedback_note"):
        st.caption(f"Your note: _{message['feedback_note']}_")


# Display all previous messages
for i, message in enumerate(st.session_state.get("messages", [])):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_feedback(i)


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
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        from openinference.instrumentation import using_attributes
        with using_attributes(
            session_id=st.session_state.session_id,
            user_id="student",
            tags=["streamlit"],
        ):
            response = get_response(prompt, st.session_state.messages)
    except ImportError:
        response = get_response(prompt, st.session_state.messages)

    st.session_state.messages.append({
        "role":    "assistant",
        "content": response.answer,
        "span_id": response.span_id,
    })
    st.session_state.conversations[st.session_state.current_chat] = (
        st.session_state.messages.copy()
    )

    with st.chat_message("assistant"):
        st.markdown(response.answer)
        display_sources(response.sources)
        render_feedback(len(st.session_state.messages) - 1)
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
