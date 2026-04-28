"""
Feedback Capture — Phoenix-Native Annotations

Shipped as working infrastructure at Session 3.1.
Students wire this into their chat display during Session 3.2
by adding st.feedback() widgets and calling submit_feedback().

Usage in main.py (students add this):
    from app.feedback import submit_feedback, get_feedback_summary

    # After displaying assistant message:
    fb = st.feedback("thumbs", key=f"fb_{i}")
    if fb is not None and message.get("span_id"):
        submit_feedback(message["span_id"], fb)

Graceful degradation: If Phoenix is not available (e.g., Community Cloud
deployment without a Phoenix server), all functions silently no-op.
The chat app continues to work without feedback capture.
"""

try:
    from phoenix.client import Client
    _PHOENIX_AVAILABLE = True
except ImportError:
    _PHOENIX_AVAILABLE = False


def _get_client():
    """Lazy Phoenix client initialization. Returns None if unavailable."""
    if not _PHOENIX_AVAILABLE:
        return None
    try:
        return Client()
    except Exception:
        return None


def submit_feedback(span_id: str, feedback_value: int, note: str = "") -> None:
    """Submit user feedback as a Phoenix span annotation.

    Args:
        span_id: The 16-char hex span ID from the pipeline trace
        feedback_value: 1 for thumbs up, 0 for thumbs down (from st.feedback)
        note: Optional explanation from the user

    Silently no-ops if Phoenix is unavailable.
    """
    client = _get_client()
    if client is None:
        return

    label = "positive" if feedback_value == 1 else "negative"
    score = 1.0 if feedback_value == 1 else 0.0

    try:
        client.annotations.add_span_annotation(
            annotation_name="user-feedback",
            annotator_kind="HUMAN",
            span_id=span_id,
            label=label,
            score=score,
            explanation=note or f"User rated response as {label}",
        )
    except Exception:
        pass  # Phoenix unavailable — silently skip


def get_feedback_summary() -> dict:
    """Get a summary of all feedback annotations from Phoenix.

    Returns:
        dict with keys: total, positive, negative, recent_negative (list of dicts)
        Returns zeros if Phoenix is unavailable.
    """
    empty = {"total": 0, "positive": 0, "negative": 0, "recent_negative": []}

    client = _get_client()
    if client is None:
        return empty

    try:
        spans_df = client.get_spans_dataframe()
    except Exception:
        return empty

    if spans_df is None or spans_df.empty:
        return empty

    # Filter spans that have user-feedback annotations
    feedback_spans = []
    for _, row in spans_df.iterrows():
        anns = row.get("annotations", [])
        if not isinstance(anns, list):
            continue
        for ann in anns:
            if isinstance(ann, dict) and ann.get("name") == "user-feedback":
                feedback_spans.append({
                    "label": ann.get("label", "unknown"),
                    "input": row.get("input.value", ""),
                    "output": row.get("output.value", ""),
                    "timestamp": str(row.get("end_time", "")),
                })

    positive = sum(1 for f in feedback_spans if f["label"] == "positive")
    negative = sum(1 for f in feedback_spans if f["label"] == "negative")
    recent_neg = [f for f in feedback_spans if f["label"] == "negative"][-5:]

    return {
        "total": len(feedback_spans),
        "positive": positive,
        "negative": negative,
        "recent_negative": recent_neg,
    }
