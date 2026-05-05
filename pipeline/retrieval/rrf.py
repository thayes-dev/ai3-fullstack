"""
rrf.py -- Reciprocal Rank Fusion (RRF) retrieval.

RRF combines ranked lists from multiple retrieval strategies into a single
ranked list. A chunk that ranks highly in *both* naive and enriched retrieval
rises to the top; a chunk that only appears in one list gets a smaller boost.

Why RRF works:
    Naive retrieval and question enrichment address the embedding gap from
    opposite directions. Naive embeds the raw question and searches answer-space.
    Enriched embeds the question and searches a pre-built question-space index.
    They have complementary failure modes — what one misses, the other often
    catches. RRF fuses their ranked outputs without requiring score calibration
    or hand-tuned weights.

The formula (Cormack et al., 2009):
    RRF_score(chunk) = Σ  1 / (k + rank(chunk, list))
                      lists
    where k=60 (standard constant that dampens the impact of very high ranks)
    and rank is 1-indexed.

    Chunks appearing in both lists accumulate contributions from both, so a
    chunk ranked #2 in naive AND #3 in enriched scores:
        1/(60+2) + 1/(60+3) ≈ 0.0161 + 0.0159 = 0.0320
    vs. a chunk only in naive at rank #1:
        1/(60+1) ≈ 0.0164

    The doubly-confirmed chunk wins even though neither individual rank is #1.

Seeding requirement:
    The enriched collection must be populated before rrf_retrieve is called.
    If it is empty, rrf_retrieve falls back to naive_retrieve with a warning
    rather than raising an exception — this keeps the app runnable during
    development.

    Seed command (~$0.50, ~3-5 min):
        uv run python -c "
        from pipeline.ingestion.chunker import chunk_document
        from pipeline.retrieval.enriched import enrich_and_store
        from pathlib import Path

        chunks = []
        for f in sorted(Path('data').glob('*.txt')):
            chunks.extend(chunk_document(f.read_text(), source=f.stem, doc_type='document'))
        enrich_and_store(chunks)
        "

Lab 2 customization points:
    - RRF_K (line ~60): lower values give more weight to rank differences
    - OVERFETCH_FACTOR (line ~61): higher values improve dedup coverage
    - The two retrieve functions (line ~80-90): swap in hyde_retrieve or
      add a third list (e.g., filtered_retrieve) for further fusion
"""

import hashlib
import logging
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)

from pipeline.retrieval.naive import naive_retrieve

logger = logging.getLogger(__name__)

# ─── CUSTOMIZABLE: RRF hyperparameters ────────────────────────────────────────
# RRF_K: damping constant from the original paper. 60 is the standard value.
#   Lower (e.g. 10) → rank differences matter more, top-1 chunks dominate.
#   Higher (e.g. 120) → smoother fusion, rank differences matter less.
# OVERFETCH_FACTOR: multiply top_k by this before calling each retriever.
#   Enriched deduplicates internally; naive does not. Over-fetching gives
#   the fusion step more candidates to work with before final dedup.
# ──────────────────────────────────────────────────────────────────────────────
RRF_K = 60
OVERFETCH_FACTOR = 3


def _chunk_key(chunk: dict) -> str:
    """Stable deduplication key for a chunk across retrieval strategies.

    Prefers (source, chunk_index) from metadata — this is reliable because
    both naive and enriched store the same source/chunk_index values for the
    same underlying text. Falls back to an MD5 of the text if metadata is
    missing, which handles hypothetical chunks from HyDE or future strategies.

    Args:
        chunk: A chunk dict with at minimum a 'metadata' key.

    Returns:
        A string key unique to this chunk's position in the corpus.
    """
    meta = chunk.get("metadata", {})
    source = meta.get("source", "")
    chunk_index = meta.get("chunk_index", "")

    if source and chunk_index != "":
        return f"{source}::{chunk_index}"

    # Fallback: hash the text content
    text = chunk.get("text", "")
    return hashlib.md5(text.encode()).hexdigest()


def rrf_retrieve(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve chunks by fusing naive and enriched ranked lists via RRF.

    Steps:
        1. Over-fetch from naive_retrieve and enriched_retrieve independently.
        2. For each chunk in each ranked list, compute its RRF contribution:
               1 / (RRF_K + rank)   where rank is 1-indexed.
        3. Sum contributions per unique chunk (chunks in both lists get both).
        4. Sort by combined RRF score descending, return top_k.

    If the enriched collection is not yet seeded, logs a warning and falls
    back to naive_retrieve alone so the app stays runnable.

    Args:
        question: The user's question.
        top_k: Number of unique chunks to return (default: 5).

    Returns:
        A list of chunk dicts (length <= top_k), each containing:
            - text: The chunk content.
            - metadata: The chunk's stored metadata.
            - score: The combined RRF score (NOT cosine similarity).
                     Higher is better. Typical range: 0.01 – 0.04.
            - rrf_sources: Which retrieval lists contributed to this chunk
                           (e.g. "naive+enriched" or "naive" or "enriched").
    """
    fetch_k = top_k * OVERFETCH_FACTOR

    # ── List 1: naive retrieval ────────────────────────────────────────────
    naive_results = naive_retrieve(question, top_k=fetch_k)

    # ── List 2: enriched retrieval (with graceful fallback) ───────────────
    try:
        from pipeline.retrieval.enriched import enriched_retrieve
        enriched_results = enriched_retrieve(question, top_k=fetch_k)
    except RuntimeError:
        logger.warning(
            "RRF: enriched collection is empty — falling back to naive retrieval only. "
            "Run enrich_and_store() to populate the enriched collection."
        )
        return naive_results[:top_k]

    # ── RRF fusion ────────────────────────────────────────────────────────
    # Track accumulated RRF scores and the contributing list names per chunk.
    rrf_scores: dict[str, float] = {}
    rrf_source_lists: dict[str, list[str]] = {}
    chunk_store: dict[str, dict] = {}

    ranked_lists = [
        ("naive", naive_results),
        ("enriched", enriched_results),
    ]

    for list_name, ranked_list in ranked_lists:
        for rank_0, chunk in enumerate(ranked_list):
            rank_1 = rank_0 + 1  # RRF uses 1-indexed ranks
            key = _chunk_key(chunk)

            contribution = 1.0 / (RRF_K + rank_1)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + contribution
            rrf_source_lists.setdefault(key, []).append(list_name)

            # Store the first time we see this chunk (naive is list 1,
            # so naive's text/metadata win on ties — doesn't matter much)
            if key not in chunk_store:
                chunk_store[key] = chunk

    # ── Sort and annotate ─────────────────────────────────────────────────
    sorted_keys = sorted(
        rrf_scores.keys(),
        key=lambda k: rrf_scores[k],
        reverse=True,
    )

    results = []
    for key in sorted_keys[:top_k]:
        chunk = dict(chunk_store[key])  # shallow copy — don't mutate the cache
        chunk["score"] = rrf_scores[key]
        chunk["rrf_score"] = rrf_scores[key]
        chunk["rrf_sources"] = "+".join(rrf_source_lists[key])
        results.append(chunk)

    return results
