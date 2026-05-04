"""
Feedback Capture — Phoenix-Native Annotations

Shipped as working infrastructure at Session 3.1.
Students wire this into their chat display during Session 3.2
by adding st.feedback() widgets and calling submit_feedback().

Graceful degradation: If Phoenix is not available the app continues
to work without feedback capture.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from phoenix.client import Client
    _PHOENIX_AVAILABLE = True
except ImportError:
    _PHOENIX_AVAILABLE = False

_PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "ai3")


def _get_client():
    if not _PHOENIX_AVAILABLE:
        return None
    try:
        return Client()
    except Exception:
        return None


def submit_feedback(span_id: str, feedback_value: int, note: str = "") -> None:
    """Submit user feedback as a Phoenix span annotation.

    Args:
        span_id: 16-char hex span ID from the pipeline trace
        feedback_value: 1 = thumbs up, 0 = thumbs down
        note: Optional explanation from the user
    """
    client = _get_client()
    if client is None:
        return
    label = "positive" if feedback_value == 1 else "negative"
    score = 1.0  if feedback_value == 1 else 0.0
    try:
        client.spans.add_span_annotation(
            annotation_name="user-feedback",
            annotator_kind="HUMAN",
            span_id=span_id,
            label=label,
            score=score,
            explanation=note or f"User rated response as {label}",
        )
    except Exception:
        pass


def get_feedback_summary() -> dict:
    """Return counts and recent negative entries from Phoenix annotations."""
    empty = {"total": 0, "positive": 0, "negative": 0, "recent_negative": []}
    client = _get_client()
    if client is None:
        return empty
    try:
        spans_df = client.spans.get_spans_dataframe(project_name=_PROJECT_NAME)
        if spans_df is None or spans_df.empty:
            return empty
        ann_df = client.spans.get_span_annotations_dataframe(
            spans_dataframe=spans_df,
            project_identifier=_PROJECT_NAME,
            include_annotation_names=["user-feedback"],
        )
    except Exception:
        return empty
    if ann_df is None or ann_df.empty:
        return empty

    input_col  = "attributes.input.value"
    output_col = "attributes.output.value"
    feedback_spans = []
    for span_id, row in ann_df.iterrows():
        label = row.get("result.label", "unknown")
        span_input, span_output = "", ""
        if span_id in spans_df.index:
            sr = spans_df.loc[span_id]
            span_input  = str(sr.get(input_col,  ""))
            span_output = str(sr.get(output_col, ""))
        feedback_spans.append({
            "label":     label,
            "input":     span_input,
            "output":    span_output,
            "timestamp": str(row.get("created_at", "")),
        })

    positive   = sum(1 for f in feedback_spans if f["label"] == "positive")
    negative   = sum(1 for f in feedback_spans if f["label"] == "negative")
    recent_neg = [f for f in feedback_spans if f["label"] == "negative"][-5:]
    return {"total": len(feedback_spans), "positive": positive,
            "negative": negative, "recent_negative": recent_neg}
