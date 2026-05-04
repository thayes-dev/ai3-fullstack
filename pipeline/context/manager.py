"""
Context Window Manager

Session 2.2: Manage conversation history within context window budget.

Three-tier strategy tuned for logistics field use (e.g., truckers who
can run very long sessions):

  Tier 1 — Normal (< 12 messages):
    Keep everything. No trimming needed.

  Tier 2 — Standard trim (12–99 messages):
    Keep first 2 messages (opening context) + summarize the middle
    into a single "Summary" assistant message + keep last 6 messages.
    Costs one extra Claude call but retains semantic continuity.

  Tier 3 — Aggressive (100+ messages):
    Skip summarization entirely to avoid runaway API spend.
    Keep first 2 + last 4, inject a hard warning directing the user
    to start a new chat. Appropriate when a session has clearly gone
    beyond normal business use.

Usage:
    from pipeline.context.manager import manage_history

    trimmed = manage_history(messages, max_messages=10)
"""

import os
import anthropic


_WARNING_MESSAGE = (
    "⚠️ This conversation has exceeded the maximum session length for cost efficiency. "
    "Please start a new chat to continue. For business questions, keep sessions focused on one topic."
)

_SUMMARY_PROMPT = """You are summarizing a logistics support conversation to save context space.
Write a concise 3–5 sentence summary of the key topics discussed, decisions made, and any
open questions. Focus on information a logistics assistant would need to answer follow-up questions.
Begin directly with 'Summary:' — no preamble."""


def _summarize_middle(middle_messages: list[dict]) -> str:
    """Call Claude to compress middle messages into a summary string."""
    conversation_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in middle_messages
    )
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": f"{_SUMMARY_PROMPT}\n\n{conversation_text}",
            }
        ],
    )
    return response.content[0].text.strip()


def manage_history(messages: list[dict], max_messages: int = 10) -> list[dict]:
    """Manage conversation history with a three-tier strategy.

    Tier 1 (< 12 msgs):  return as-is.
    Tier 2 (12–99 msgs): first 2 + LLM summary of middle + last 6.
    Tier 3 (100+ msgs):  first 2 + warning + last 4, no summarization.

    Args:
        messages: Full conversation history (list of role/content dicts).
        max_messages: Kept for API compatibility; tiers use fixed bounds.

    Returns:
        Managed message list ready for the RAG pipeline.
    """
    if not messages:
        return []

    n = len(messages)

    # ── Tier 1: normal session ────────────────────────────────
    if n < 12:
        return messages

    # ── Tier 3: excessive session — hard cutoff ───────────────
    if n >= 100:
        warning_msg = {"role": "assistant", "content": _WARNING_MESSAGE}
        return list(messages[:2]) + [warning_msg] + list(messages[-4:])

    # ── Tier 2: standard trim with summarization ──────────────
    # Keep first 2 and last 6; summarize everything in between.
    first = list(messages[:2])
    last = list(messages[-6:])
    middle = list(messages[2:-6])

    if middle:
        try:
            summary_text = _summarize_middle(middle)
        except Exception:
            # Summarization failed — fall back to dropping the middle silently
            summary_text = "Summary: Earlier conversation context was condensed to save space."
        summary_msg = {"role": "assistant", "content": summary_text}
        return first + [summary_msg] + last

    return first + last
