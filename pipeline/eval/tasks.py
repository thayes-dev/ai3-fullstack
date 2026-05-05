"""
tasks.py -- Pipeline task closures for Phoenix experiments.

Lab 2 adds rrf_task -- fuses naive + enriched via Reciprocal Rank Fusion.
Run all three in run_experiment.py for a naive vs. hyde vs. rrf comparison.
"""

from pipeline.retrieval.naive import naive_retrieve, build_prompt
from pipeline.generation.generate import call_claude_with_usage

TOP_K = 5


def _run_pipeline(question: str, retrieve_fn) -> dict:
    chunks = retrieve_fn(question, TOP_K)
    system_prompt, user_message = build_prompt(question, chunks)
    result = call_claude_with_usage(
        prompt=user_message,
        system_prompt=system_prompt,
        temperature=0.0,
    )
    return {
        "chunks": chunks,
        "answer": result["text"],
    }


def naive_task(input: dict) -> dict:
    """Run the naive RAG pipeline on one dataset example."""
    question = input["question"]
    result = _run_pipeline(question, naive_retrieve)
    return {"question": question, **result}


def hyde_task(input: dict) -> dict:
    """Run the HyDE RAG pipeline on one dataset example."""
    from pipeline.retrieval.hyde import hyde_retrieve
    question = input["question"]
    result = _run_pipeline(question, hyde_retrieve)
    return {"question": question, **result}


def rrf_task(input: dict) -> dict:
    """Run the RRF RAG pipeline on one dataset example.

    Fuses naive_retrieve and enriched_retrieve ranked lists via
    Reciprocal Rank Fusion (k=60). Chunks confirmed by both strategies
    score higher than those appearing in only one list.

    Requires the enriched collection to be seeded first.
    See pipeline/retrieval/rrf.py for the seed command.
    """
    from pipeline.retrieval.rrf import rrf_retrieve
    question = input["question"]
    result = _run_pipeline(question, rrf_retrieve)
    return {"question": question, **result}
