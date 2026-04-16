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
      answer_addresses_question(input, output, expected) -> bool
      "Does the generated answer align with the expected answer?"

Students: read the docstrings, then fill in the function bodies during class.
"""

import anthropic


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
# Pattern B: LLM-as-judge evaluator
# ---------------------------------------------------------------------------
# Judge prompt template — the instruction we hand the Claude judge.
# Placeholders get filled in by the evaluator at call time.
JUDGE_TEMPLATE = """You are grading a RAG system's answer.

Question: {prompt}
Expected answer: {expected}
Generated answer: {response}

Does the generated answer substantively address the question
AND align with the expected answer?

Respond with exactly one line:
PASS: <brief reason>
or
FAIL: <brief reason>"""


def answer_addresses_question(input: dict, output: dict, expected: dict) -> bool:
    """Does the generated answer align with the expected answer?

    Uses Claude Haiku 4.5 as the judge. The judge sees the question, the
    ground-truth expected answer, AND the generated answer — then returns
    PASS or FAIL based on alignment.

    This is the "LLM-as-judge" pattern: cheaper and more scalable than human
    review, more semantic than string matching.

    Args:
        input: The dataset input dict. Has a `question` key.
        output: The task output dict. Has an `answer` key.
        expected: The ground-truth dict. Has an `expected_answer` key.

    Returns:
        True if the judge returns PASS, False otherwise.

    Hint for students:
        1. Format JUDGE_TEMPLATE with the question, expected, and generated answer.
           (Cap the generated answer at 2000 chars to control token cost.)
        2. Call the Claude Haiku 4.5 model with max_tokens=100.
        3. Parse the first line of the response — if it starts with "PASS"
           (case-insensitive), return True. Otherwise return False.
    """
    # We'll build this together in class.
    pass
