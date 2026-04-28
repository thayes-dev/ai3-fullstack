"""
Context Assembler -- Canonical implementations for query rewriting and context assembly.

Two functions:
  - contextualize_query(): Rewrite follow-up questions for stateless retrieval
  - assemble_context(): Organize retrieved chunks into coherent reading order

Both functions are fully working infrastructure. For Lab 2, look for
CUSTOMIZABLE breadcrumbs marking the parts you can tune for your use case.

Usage:
    from pipeline.context.assembler import contextualize_query, assemble_context

    standalone = contextualize_query(history, "How many days do I get?")
    context_str = assemble_context(chunks)
"""

from collections import defaultdict

from pipeline.generation.generate import call_claude


# ─── CUSTOMIZABLE: Query rewriting prompt ──────────────
# Change the system prompt or user message format to
# improve rewriting for your specific use case.
# ───────────────────────────────────────────────────────

_REWRITE_SYSTEM_PROMPT = (
    "You are a query rewriter. Given a conversation history and a follow-up "
    "question, rewrite the follow-up as a standalone question that captures "
    "the full context.\n"
    "Return ONLY the rewritten question — no explanation, no preamble.\n"
    "If the question is already standalone, return it unchanged."
)


def contextualize_query(history: list[dict], user_message: str) -> str:
    """Rewrite a follow-up question so it stands alone for retrieval.

    When a user asks "How many days do I get?" after discussing vacation
    policy, retrieval needs the full question: "How many vacation days
    does a Northbrook employee receive?"

    If the message is already self-contained, return it unchanged.

    Args:
        history: Previous conversation messages (list of role/content dicts).
        user_message: The user's latest message.

    Returns:
        A rewritten query that stands alone for retrieval,
        OR the original user_message if no rewrite is needed.
    """
    # First message — no history to resolve against
    if not history:
        return user_message

    # Limit to last 6 messages (3 exchanges) to keep the rewriting call small
    recent = history[-6:]

    # Format history as readable lines
    history_lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_lines.append(f"{role}: {msg['content']}")

    prompt = (
        "Conversation history:\n"
        + "\n".join(history_lines)
        + f"\n\nFollow-up question: {user_message}"
    )

    rewritten = call_claude(
        prompt=prompt,
        system_prompt=_REWRITE_SYSTEM_PROMPT,
        temperature=0.0,
        max_tokens=256,
    )

    return rewritten.strip()


# ─── CUSTOMIZABLE: Context assembly layout ─────────────
# Adjust grouping, headers, or gap markers to change how
# retrieved context is presented to the model.
# ───────────────────────────────────────────────────────


def naive_assemble(chunks: list[dict]) -> str:
    """Off-state control for assemble_context — bare similarity-order concat.

    Used by the Session 2.2 Phoenix experiments as the "no assembly" baseline
    so we can measure what assemble_context's grouping/sorting/gap-marking
    actually contributes. Preserves the order retrieval returned (descending
    similarity), separates chunks with `---`, and adds NO source headers,
    NO chunk-index sorting, and NO gap markers.

    Args:
        chunks: List of chunk dicts (only `text` is read).

    Returns:
        Joined chunk text in retrieval order, separated by `\\n\\n---\\n\\n`.
    """
    if not chunks:
        return ""
    return "\n\n---\n\n".join(c["text"] for c in chunks)


def assemble_context(
    chunks: list[dict], gap_marker: str = "[...content omitted...]"
) -> str:
    """Assemble retrieved chunks into coherent reading order.

    Steps:
      1. Group chunks by source document (metadata['source'])
      2. Sort each group by chunk index (metadata['chunk_index'])
      3. For each group, build a section:
         - Header: "--- Source: {source} ---"
         - For each chunk: if chunk_index is not consecutive
           with the previous chunk, insert the gap_marker
         - Then the chunk text
      4. Join all sections with double newlines
      5. Return the assembled context string

    Args:
        chunks: List of chunk dicts with keys: text, metadata (source, chunk_index), score
        gap_marker: String to insert between non-consecutive chunks.

    Returns:
        Assembled context string with document grouping, reading order, and gap markers.
    """
    if not chunks:
        return ""

    # Group chunks by source document
    groups: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        source = chunk["metadata"]["source"]
        groups[source].append(chunk)

    # Sort each group by chunk_index
    for source in groups:
        groups[source].sort(key=lambda c: c["metadata"]["chunk_index"])

    # Build sections
    sections = []
    for source, source_chunks in groups.items():
        lines = [f"--- Source: {source} ---"]
        prev_index = None

        for chunk in source_chunks:
            current_index = chunk["metadata"]["chunk_index"]

            # Insert gap marker for non-consecutive chunks
            if prev_index is not None and current_index != prev_index + 1:
                lines.append(gap_marker)

            lines.append(chunk["text"])
            prev_index = current_index

        sections.append("\n".join(lines))

    return "\n\n".join(sections)
