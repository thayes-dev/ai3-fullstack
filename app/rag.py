"""
rag.py -- Pipeline integration for Streamlit chat app.

INSTRUCTOR-MANAGED through Session 3.1.
After Session 3.1, this file is yours to customize for Lab 2.
See the marked sections below for customization points.

This module wires the RAG pipeline into the Streamlit interface.
main.py imports: from app.rag import get_response, ChatResponse

Current version: Session 2.2 (context-aware RAG)
    Changes from 2.1:
    - Added conversation history management (manage_history)
    - Added query rewriting for multi-turn retrieval (contextualize_query)
    - Added context assembly with document grouping (assemble_context)
    - Prompt now includes prior conversation for continuity
    - ChatResponse includes rewritten_query for transparency
    - 7 marked customization sections for Lab 2
"""

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above app/)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


# ─── RETRIEVAL STRATEGY ───────────────────────────────────────
# Which retrieval function to use for finding relevant chunks.
# Default: naive_retrieve (pure semantic similarity).
#
# For Lab 2, swap this import to change your retrieval strategy:
#   from pipeline.retrieval.hyde import hyde_retrieve as retrieve
#   from pipeline.retrieval.enriched import enriched_retrieve as retrieve
#
# The retrieve function must accept (question: str, top_k: int)
# and return list[dict] with keys: text, metadata, score.
# ──────────────────────────────────────────────────────────────
from pipeline.retrieval.naive import naive_retrieve as retrieve

from pipeline.generation.generate import call_claude
from pipeline.context.assembler import contextualize_query, assemble_context
from pipeline.context.manager import manage_history


@dataclass
class ChatResponse:
    """Structured response from the RAG pipeline.

    Attributes:
        answer: The generated answer text from Claude.
        sources: Retrieved chunks used as context. Each dict contains
                 'text', 'metadata', and 'score' keys.
        rewritten_query: The query after contextualization. Shows how
                         the pipeline interpreted a follow-up question
                         for retrieval (may match original if standalone).
    """

    answer: str
    sources: list[dict] = field(default_factory=list)
    rewritten_query: str = ""


# ─── SYSTEM PROMPT ─────────────────────────────────────────────
# Persona, tone, and grounding rules for Claude.
# Customize this to change how the assistant behaves:
#   - Change the persona (e.g., formal, casual, technical)
#   - Tighten or loosen grounding rules
#   - Add domain-specific instructions
# ───────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a helpful assistant for Northbrook Partners employees.
Answer questions using ONLY the provided source documents.
If the sources don't contain enough information, say so.
If prior conversation is shown, build on it — don't repeat previous answers."""


def get_response(question: str, messages: list[dict]) -> ChatResponse:
    """Get a grounded response from the RAG pipeline.

    Pipeline steps:
      1. Manage history — trim conversation to fit context budget
      2. Contextualize — rewrite follow-ups into standalone queries
      3. Retrieve — find relevant chunks using the rewritten query
      4. Assemble — organize chunks into coherent reading order
      5. Build prompt — combine history, sources, and question
      6. Generate — call Claude with the assembled prompt

    Args:
        question: The user's current question.
        messages: Conversation history (list of role/content dicts).

    Returns:
        A ChatResponse with the answer, supporting sources, and
        the rewritten query used for retrieval.
    """

    # ─── HISTORY MANAGEMENT ────────────────────────────────────
    # Trim conversation history to fit within context budget.
    # Default: keep the last 10 messages (5 exchanges).
    #
    # Alternatives to explore:
    #   - Keep first + last messages (preserve opening context)
    #   - Summarize old messages instead of dropping them
    #   - Adjust max_messages based on message length
    # ──────────────────────────────────────────────────────────
    managed_history = manage_history(messages, max_messages=10)

    # ─── QUERY REWRITING ──────────────────────────────────────
    # Rewrite follow-up questions so they stand alone for retrieval.
    # e.g., "How many days?" after discussing PTO becomes
    #        "How many PTO days does a Northbrook employee receive?"
    #
    # The rewriting prompt lives in pipeline/context/assembler.py.
    # Customize it there to change rewriting behavior.
    # ──────────────────────────────────────────────────────────
    rewritten = contextualize_query(managed_history, question)

    # ─── RETRIEVAL PARAMETERS ─────────────────────────────────
    # How many chunks to retrieve and quality thresholds.
    # top_k: number of chunks to fetch (more = broader context,
    #         but costs more tokens and may add noise).
    #
    # After retrieval, you could also filter by score threshold:
    #   sources = [s for s in sources if s["score"] > 0.35]
    # ──────────────────────────────────────────────────────────
    sources = retrieve(rewritten, top_k=5)

    # Handle empty retrieval
    if not sources:
        return ChatResponse(
            answer="I couldn't find relevant information in the Northbrook documents.",
            sources=[],
            rewritten_query=rewritten,
        )

    # ─── CONTEXT ASSEMBLY ─────────────────────────────────────
    # Organize retrieved chunks into coherent reading order.
    # Groups by source document, sorts by chunk index, inserts
    # gap markers between non-consecutive chunks.
    #
    # The assembly logic lives in pipeline/context/assembler.py.
    # Customize it there to change grouping, ordering, or format.
    # ──────────────────────────────────────────────────────────
    assembled = assemble_context(sources)

    # Build the prompt with conversation context
    sections = []

    # Include recent conversation for continuity (last 3 exchanges = 6 messages)
    recent = managed_history[-6:] if managed_history else []
    if recent:
        conversation_lines = []
        for msg in recent:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            conversation_lines.append(f"{role_label}: {msg['content']}")
        sections.append("## Conversation So Far\n" + "\n\n".join(conversation_lines))

    sections.append("## Sources\n" + assembled)

    # Use the original question, NOT the rewritten query.
    # The rewritten query was for retrieval only. Claude should
    # answer what the user actually asked.
    sections.append("## Current Question\n" + question)

    user_message = "\n\n".join(sections)

    # ─── GENERATION SETTINGS ──────────────────────────────────
    # Model, temperature, and token limits for Claude.
    # temperature=0.0 gives deterministic, grounded answers.
    #
    # Options to explore:
    #   - temperature=0.3 for slightly more varied responses
    #   - max_tokens=2048 for longer answers
    #   - model="claude-haiku-4-5" for faster/cheaper responses
    # ──────────────────────────────────────────────────────────
    answer = call_claude(user_message, system_prompt=_SYSTEM_PROMPT, temperature=0.0)

    return ChatResponse(answer=answer, sources=sources, rewritten_query=rewritten)
