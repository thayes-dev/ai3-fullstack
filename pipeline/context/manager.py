"""
Context Window Manager

Session 2.2: Manage conversation history within context window budget.

Strategy: simple message-count sliding window.
  - Keep the last N messages (default: 10 = 5 exchanges)
  - Old messages are dropped entirely
  - For production: consider summarization-based compression

Usage:
    from pipeline.context.manager import manage_history

    trimmed = manage_history(messages, max_messages=10)

We'll build this function together in class.
"""


def manage_history(messages: list[dict], max_messages: int = 10) -> list[dict]:
    """Truncate conversation history to fit within context budget.

    Keeps the most recent messages. Old messages are dropped entirely.
    max_messages should be even to preserve complete user/assistant pairs.

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
    # PASSTHROUGH DEFAULT — returns messages unchanged
    return messages
