"""
Context Window Manager

Session 2.2: Manage conversation history within context window budget.

Chat history grows with every exchange. Without management, it will
eventually exceed the model's context window — or waste tokens on
irrelevant early turns. This module provides a simple sliding-window
strategy that keeps the most recent messages.

Three strategies worth knowing (Lab 2 candidates):

  1. **Keep last N** (implemented here)
     - Drop oldest messages, keep the most recent.
     - Simple, predictable, zero API calls.
     - Tradeoff: loses early context entirely.

  2. **Keep first + last**
     - Preserve the first 2 messages (system framing / opening question)
       plus the last N. Everything in the middle is dropped.
     - Tradeoff: still loses middle context; slightly more complex.

  3. **Summarize**
     - When history exceeds the budget, call the LLM to compress older
       messages into a summary message, then prepend it.
     - Tradeoff: adds latency and cost per summarization call, but
       retains the *meaning* of the full conversation.

Usage:
    from pipeline.context.manager import manage_history

    trimmed = manage_history(messages, max_messages=10)
"""


def manage_history(messages: list[dict], max_messages: int = 10) -> list[dict]:
    """Truncate conversation history to fit within context budget.

    Keeps the most recent messages. Old messages are dropped entirely.
    max_messages is rounded down to the nearest even number so we never
    split a user/assistant pair mid-exchange.

    Args:
        messages: Full conversation history (list of role/content dicts).
        max_messages: Maximum number of messages to keep (default: 10,
                      which is 5 complete exchanges).

    Returns:
        Truncated message list (last max_messages messages).

    Notes:
        - Always keep the most recent messages
        - Does NOT include the current user question (that is added after)
        - In production, consider summarization for long conversations
    """
    # Guard: empty or None → empty list
    if not messages:
        return []

    # ─── CUSTOMIZABLE: History management strategy ─────────
    # Default: simple sliding window (keep last N messages).
    # Alternatives you could implement for Lab 2:
    #   - Keep first 2 + last N (preserves conversation opening)
    #   - Summarize old messages with an LLM call
    #   - Token-based budget instead of message count
    # ───────────────────────────────────────────────────────

    # Round down to even so we don't split a user/assistant pair
    max_messages = max_messages - (max_messages % 2)

    # If history fits within budget, return as-is
    if len(messages) <= max_messages:
        return messages

    # Sliding window: keep the last max_messages entries
    return messages[-max_messages:]
