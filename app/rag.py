"""
rag.py -- Pipeline integration for Streamlit chat app.

INSTRUCTOR-MANAGED through Session 3.1. CODE FREEZE in effect after this version.
After Session 3.1, this file is yours to customize for Lab 2.
See the marked sections below for customization points.

This module wires the RAG pipeline into the Streamlit interface.
main.py imports: from app.rag import get_response, ChatResponse

Current version: Session 3.1 (safety-hardened)
    Changes from 2.1:
    - Added conversation history management (manage_history)
    - Added query rewriting for multi-turn retrieval (contextualize_query)
    - Added context assembly with document grouping (assemble_context)
    - Prompt now includes prior conversation for continuity
    - ChatResponse includes rewritten_query for transparency
    - 7 marked customization sections for Lab 2

    Session 3.1 changes:
    - Added input validation (defense layer 1)
    - Replaced manual system prompt with hardened prompt (defense layer 2)
    - Added output validation (defense layer 3)
    - Added span_id capture for Phoenix feedback annotations
    - ChatResponse includes span_id for feedback widget linking
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
from pipeline.safety.guard import validate_input, build_hardened_prompt, validate_output
from opentelemetry import trace


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
    span_id: str = ""



def get_response(question: str, messages: list[dict]) -> ChatResponse:
    """Get a grounded response from the RAG pipeline with safety guards.

    Pipeline steps:
      1. Capture span_id for Phoenix feedback annotations
      2. Validate input (defense layer 1)
      3. Manage history — trim conversation to fit context budget
      4. Contextualize — rewrite follow-ups into standalone queries
      5. Retrieve — find relevant chunks using the rewritten query
      6. Assemble — organize chunks into coherent reading order
      7. Build hardened prompt (defense layer 2)
      8. Generate — call Claude with the hardened prompt
      9. Validate output (defense layer 3)

    Args:
        question: The user's current question.
        messages: Conversation history (list of role/content dicts).

    Returns:
        A ChatResponse with the answer, supporting sources,
        the rewritten query used for retrieval, and span_id.
    """

    # Capture span for Phoenix feedback annotations
    span = trace.get_current_span()
    ctx = span.get_span_context()
    span_id = format(ctx.span_id, '016x') if ctx.span_id else ""

    # --- INPUT VALIDATION (defense layer 1) ---
    input_ok, input_reason = validate_input(question)
    if not input_ok:
        return ChatResponse(
            answer=input_reason,
            sources=[],
            rewritten_query="",
            span_id=span_id,
        )

    # ─── HISTORY MANAGEMENT (customization section 3 of 7) ────
    # Trim conversation history to fit within context budget.
    # Default: keep the last 10 messages (5 exchanges).
    #
    # Alternatives to explore:
    #   - Keep first + last messages (preserve opening context)
    #   - Summarize old messages instead of dropping them
    #   - Adjust max_messages based on message length
    # ──────────────────────────────────────────────────────────
    managed_history = manage_history(messages, max_messages=10)

    # ─── QUERY REWRITING (customization section 4 of 7) ──────
    # Rewrite follow-up questions so they stand alone for retrieval.
    # e.g., "How many days?" after discussing PTO becomes
    #        "How many PTO days does a Northbrook employee receive?"
    #
    # The rewriting prompt lives in pipeline/context/assembler.py.
    # Customize it there to change rewriting behavior.
    # ──────────────────────────────────────────────────────────
    rewritten = contextualize_query(managed_history, question)

    # ─── RETRIEVAL PARAMETERS (customization section 5 of 7) ─
    # How many chunks to retrieve and quality thresholds.
    # top_k: number of chunks to fetch (more = broader context,
    #         but costs more tokens and may add noise).
    #
    # After retrieval, you could also filter by score threshold:
    #   sources = [s for s in sources if s["score"] > 0.35]
    # ──────────────────────────────────────────────────────────
    sources = retrieve(rewritten, top_k=5)

    if not sources:
        return ChatResponse(
            answer="I couldn't find relevant information in the Northbrook documents.",
            sources=[],
            rewritten_query=rewritten,
            span_id=span_id,
        )

    # ─── CONTEXT ASSEMBLY (customization section 6 of 7) ─────
    # Organize retrieved chunks into coherent reading order.
    # Groups by source document, sorts by chunk index, inserts
    # gap markers between non-consecutive chunks.
    #
    # The assembly logic lives in pipeline/context/assembler.py.
    # Customize it there to change grouping, ordering, or format.
    # ──────────────────────────────────────────────────────────
    assembled = assemble_context(sources)

    # --- SYSTEM PROMPT HARDENING (defense layer 2) ---
    # Build prompt sections: conversation history + assembled context + question
    sections = []
    recent = managed_history[-6:] if managed_history else []
    if recent:
        conversation_lines = []
        for msg in recent:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            conversation_lines.append(f"{role_label}: {msg['content']}")
        sections.append("## Conversation So Far\n" + "\n\n".join(conversation_lines))

    sections.append(assembled)  # Context goes into the hardened prompt

    full_context = "\n\n".join(sections)
    system_prompt = build_hardened_prompt(full_context)

    # The user message is just the current question (not the full context)
    user_message = question

    # ─── GENERATION SETTINGS (customization section 7 of 7) ──
    # Model, temperature, and token limits for Claude.
    # temperature=0.0 gives deterministic, grounded answers.
    #
    # Options to explore:
    #   - temperature=0.3 for slightly more varied responses
    #   - max_tokens=2048 for longer answers
    #   - model="claude-haiku-4-5" for faster/cheaper responses
    # ──────────────────────────────────────────────────────────
    answer = call_claude(user_message, system_prompt=system_prompt, temperature=0.0)

    # --- OUTPUT VALIDATION (defense layer 3) ---
    source_names = [s.get("metadata", {}).get("source", "") for s in sources]
    output_ok, output_reason = validate_output(answer, source_names)
    if not output_ok:
        return ChatResponse(
            answer=output_reason,
            sources=sources,
            rewritten_query=rewritten,
            span_id=span_id,
        )

    return ChatResponse(answer=answer, sources=sources, rewritten_query=rewritten, span_id=span_id)
