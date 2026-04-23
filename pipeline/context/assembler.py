"""
Context Assembler

Session 2.2: Query rewriting and context assembly for RAG.

Two functions:
  - contextualize_query(): Rewrite follow-up questions for stateless retrieval
  - assemble_context(): Organize retrieved chunks into coherent reading order

Usage:
    from pipeline.context.assembler import contextualize_query, assemble_context

    standalone = contextualize_query(history, "How many days do I get?")
    context_str = assemble_context(chunks)

We'll build these functions together in class.
"""

from pipeline.generation.generate import call_claude


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
    # PASSTHROUGH DEFAULT — app works without rewriting
    return user_message


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

    # PASSTHROUGH DEFAULT — app works with flat concatenation
    return "\n\n".join(chunk["text"] for chunk in chunks)
