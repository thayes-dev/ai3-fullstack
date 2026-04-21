"""
rag.py -- Pipeline integration for Streamlit chat app.

INSTRUCTOR-MANAGED -- Students should not modify this file.

This module wires the RAG pipeline into the Streamlit interface.
main.py imports: from app.rag import get_response, ChatResponse

Current version: Session 2.1 (basic RAG)
    - Retrieves sources via naive semantic search
    - Builds a grounded prompt with source context
    - Calls Claude with the assembled prompt

Session 2.2 will upgrade this module with:
    - Context assembly from conversation history
    - Token counting and dynamic context window management
    - Message history integration for multi-turn grounded chat
"""

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above app/)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

from pipeline.retrieval.naive import naive_retrieve, build_prompt
from pipeline.generation.generate import call_claude


@dataclass
class ChatResponse:
    """Structured response from the RAG pipeline.

    Attributes:
        answer: The generated answer text from Claude.
        sources: Retrieved chunks used as context. Each dict contains
                 'text', 'metadata', and 'score' keys.
    """

    answer: str
    sources: list[dict] = field(default_factory=list)


def get_response(question: str, messages: list[dict]) -> ChatResponse:
    """Get a grounded response from the RAG pipeline.

    Retrieves relevant Northbrook documents, builds a grounded prompt
    with source context, and calls Claude to generate an answer.

    Args:
        question: The user's current question.
        messages: Conversation history (list of role/content dicts).
                  Currently unused -- messages parameter available for
                  future context management (Session 2.2).

    Returns:
        A ChatResponse with the answer and supporting sources.
    """
    # Step 1: Retrieve relevant chunks via semantic search
    sources = naive_retrieve(question, top_k=5)

    # Step 2: Handle empty retrieval
    if not sources:
        return ChatResponse(
            answer="I couldn't find relevant information in the Northbrook documents.",
            sources=[],
        )

    # Step 3: Build grounded prompt with source context
    system_prompt, user_message = build_prompt(question, sources)

    # Step 4: Generate answer from Claude
    answer = call_claude(user_message, system_prompt=system_prompt, temperature=0.0)

    return ChatResponse(answer=answer, sources=sources)
