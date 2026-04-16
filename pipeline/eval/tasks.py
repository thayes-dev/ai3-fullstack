"""
tasks.py -- Pipeline task closures for Phoenix experiments.

A Phoenix "task" is a function that takes one dataset example (a dict) and
returns a dict of output that evaluators will grade. Each task runs a full
RAG pipeline end-to-end: retrieval + prompt assembly + generation.

We expose two tasks — one per retrieval strategy — so Phoenix can run the
same golden set through both and produce a side-by-side comparison in the UI.

    client.experiments.run_experiment(dataset=..., task=naive_task, ...)
    client.experiments.run_experiment(dataset=..., task=hyde_task, ...)

Students explore by:
    - Reading the symmetric structure (both tasks share a helper)
    - Adding their own task (e.g., `enriched_task`) once they've built
      `enriched_retrieve()` in Session 1.1
    - Inspecting what `naive_task({"question": "..."})` returns locally
"""

from pipeline.retrieval.naive import naive_retrieve, build_prompt
from pipeline.generation.generate import call_claude_with_usage

# Note: hyde_retrieve is imported lazily inside hyde_task() because students
# build it during Session 1.1. On a fresh clone before 1.1, this module would
# fail to import at top level. Lazy import lets naive_task work regardless.


# The number of chunks each retrieval strategy pulls. 5 is a reasonable default
# for this corpus — small enough to keep context tight, large enough that
# multi-doc queries have a chance to find all their sources.
TOP_K = 5


def _run_pipeline(question: str, retrieve_fn) -> dict:
    """Shared helper: retrieve chunks, build the RAG prompt, call Claude.

    Both naive_task and hyde_task use this — the only difference between
    them is which retrieve function they pass in. This keeps the task
    surface symmetric so comparisons are apples-to-apples.

    Args:
        question: The user query to answer.
        retrieve_fn: A function with the same contract as `naive_retrieve`
            (takes a question + top_k, returns list of {text, metadata, score}).

    Returns:
        A dict with `chunks` (what retrieval found) and `answer` (what
        generation produced). This shape is what Phoenix passes to evaluators
        as the `output` parameter.
    """
    # Step 1: retrieval — get the top_k chunks for this question
    chunks = retrieve_fn(question, top_k=TOP_K)

    # Step 2: prompt assembly — format chunks as a context block for Claude
    system_prompt, user_message = build_prompt(question, chunks)

    # Step 3: generation — call Claude with temperature=0.0 for reproducibility
    # (so scores are stable across runs of the same experiment)
    result = call_claude_with_usage(
        prompt=user_message,
        system_prompt=system_prompt,
        temperature=0.0,
    )

    return {
        "chunks": chunks,           # Evaluators inspect this for retrieval quality
        "answer": result["text"],   # Evaluators inspect this for answer quality
    }


def naive_task(input: dict) -> dict:
    """Run the naive RAG pipeline on one dataset example.

    Phoenix calls this once per row in the dataset. The `input` parameter
    is bound BY NAME to the row's inputs dict — whatever we put in
    `inputs[i]` when we created the dataset. For us: {"question": "..."}.

    The returned dict becomes the `output` parameter that evaluators receive.

    Args:
        input: A dict like {"question": "What is the vacation policy?"}.

    Returns:
        {"question": ..., "chunks": [...], "answer": ...}
    """
    question = input["question"]
    result = _run_pipeline(question, naive_retrieve)
    return {"question": question, **result}


def hyde_task(input: dict) -> dict:
    """Run the HyDE RAG pipeline on one dataset example.

    Identical to `naive_task` except it uses `hyde_retrieve` — which first
    asks Claude to generate a hypothetical answer, then embeds THAT answer
    (not the question) to do the vector search. See Session 1.1 for why.

    Args:
        input: A dict like {"question": "What is the vacation policy?"}.

    Returns:
        {"question": ..., "chunks": [...], "answer": ...}
    """
    from pipeline.retrieval.hyde import hyde_retrieve  # lazy — see note at top

    question = input["question"]
    result = _run_pipeline(question, hyde_retrieve)
    return {"question": question, **result}
