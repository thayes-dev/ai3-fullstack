"""
evaluators.py -- Pass/fail functions that grade a task's output.

Phoenix calls each evaluator once per experiment row with parameters bound
BY NAME from the dataset and task output:

    input     -> the dataset's inputs[i] dict       (e.g., {"question": "..."})
    output    -> whatever the task returned         (e.g., {"chunks": [...], "answer": "..."})
    expected  -> the dataset's outputs[i] dict      (e.g., {"expected_answer": "...", ...})
    metadata  -> the dataset's metadata[i] dict     (optional; ids, categories, etc.)

You only declare the parameters you actually use. Phoenix figures out the rest.

Session 1.2: We build two evaluators together in class.

  Pattern A (deterministic, ~10 lines):
      retrieval_hit(output, expected) -> bool
      "Did retrieval pull the expected source document?"

  Pattern B (LLM-as-judge, ~25 lines):
      answer_addresses_question(input, output, expected) -> dict
      "Does the generated answer align with the expected answer?"
      Uses STRUCTURED OUTPUT (Pydantic + tool_use) — callback to AI-2 Session 1.2.

Students: read the docstrings, then fill in the function bodies during class.
"""

from typing import Literal

import anthropic
from pydantic import BaseModel, Field


# Claude client for the LLM judge. Haiku 4.5 is ~10x cheaper than Sonnet and
# plenty accurate for PASS/FAIL classification with a clear rubric.
_client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Pattern A: deterministic evaluator
# ---------------------------------------------------------------------------
def retrieval_hit(output: dict, expected: dict) -> bool:
    """Did retrieval pull at least one of the expected source documents?

    A deterministic evaluator — no LLM involved, just a set-membership check.
    This grades the RETRIEVAL half of the pipeline independently of the
    generation half.

    Args:
        output: What the task returned. Has a `chunks` key — a list of dicts
            with `metadata.source` for each retrieved chunk.
        expected: The ground-truth entry from the golden set. Has an
            `expected_source` key — a list of filenames that SHOULD be
            retrieved for this query.

    Returns:
        True if any expected source appears in the retrieved set.

    Hint for students:
        1. Pull the list of retrieved sources from output["chunks"].
           Each chunk has source in chunk["metadata"]["source"].
        2. Pull the list of expected sources from expected["expected_source"].
        3. Return True if any expected source is in the retrieved list.
    """
    # We'll build this together in class.
    pass


# ---------------------------------------------------------------------------
# Pattern B: LLM-as-judge with STRUCTURED OUTPUT
# ---------------------------------------------------------------------------
# Callback to AI-2 Session 1.2: we learned there that parsing LLM text output
# with string-munging is brittle. Pydantic + a tool-use schema forces the
# model to return a shape we can trust — zero string parsing required.
class JudgeVerdict(BaseModel):
    """The judge's structured verdict. Pydantic validates the shape."""

    verdict: Literal["PASS", "FAIL"]
    reason: str = Field(description="Brief justification for the verdict")


# Judge prompt template. Note: no format instructions. The schema (tool_use)
# is the contract — the prompt only has to ask for the judgment.
JUDGE_TEMPLATE = """You are grading a RAG system's answer.

Question: {prompt}
Expected answer: {expected}
Generated answer: {response}

Decide whether the generated answer substantively addresses the question
AND aligns with the expected answer. Provide a brief reason."""


def answer_addresses_question(input: dict, output: dict, expected: dict) -> dict:
    """Does the generated answer align with the expected answer?

    Uses Claude Haiku 4.5 as the judge via STRUCTURED OUTPUT. The judge is
    handed a `record_verdict` tool whose schema is the `JudgeVerdict` Pydantic
    model — Claude can only respond by "calling" the tool with a valid verdict.
    No brittle PASS/FAIL string parsing.

    Returning a dict (not bool) lets Phoenix log score + label + explanation
    for every row — click any failed row in the UI and see WHY the judge
    rejected it.

    Args:
        input: The dataset input dict. Has a `question` key.
        output: The task output dict. Has an `answer` key.
        expected: The ground-truth dict. Has an `expected_answer` key.

    Returns:
        Dict shaped for Phoenix: {"score", "label", "explanation"}.
        Phoenix renders all three in the experiment results table.

    Hint for students:
        1. Format JUDGE_TEMPLATE with question, expected, generated answer.
           (Cap the generated answer at 2000 chars to control token cost.)
        2. Call Claude Haiku 4.5 with the record_verdict tool forced via
           tool_choice={"type": "tool", "name": "record_verdict"}.
           The tool's input_schema is JudgeVerdict.model_json_schema().
        3. Pull the tool_use content block from result.content, then
           validate it with JudgeVerdict(**tool_block.input).
        4. Return {"score": 1 if PASS else 0, "label": verdict, "explanation": reason}.
    """
    # We'll build this together in class.
    pass
