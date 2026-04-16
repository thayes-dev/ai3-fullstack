"""
build_embedding_cache.py -- One-time cache builder for the 3D PCA visualization.

This script computes every embedding the viz notebook needs, fits a 3D PCA on
the mixed dataset, and pickles the whole bundle. Students never run this —
they just load `notebooks/_cache/pca_viz_cache.pkl` from a fresh clone.

Why we cache:
    1. Determinism — students see identical geometry in every class
    2. Zero API calls during demo — no pauses, no rate-limit surprises
    3. PCA projection is fit ONCE on the mixed dataset so question-space and
       answer-space each own their own axes

What gets computed:
    - 173 corpus chunks: pulled from ChromaDB (already embedded)
    - 10 golden queries: one Voyage embed per query (raw)
    - 10 HyDE vectors: Claude generates a hypothetical answer per query, then
      Voyage embeds each one
    - 519 enrichment question vectors: for each chunk, Claude generates 3
      questions the chunk answers, then Voyage embeds each question
    - Fitted PCA(n_components=3) on the stacked matrix (173 + 10 + 10 + 519)
    - 3D projections for all of the above

Run from repo root:
    uv run python notebooks/scripts/build_embedding_cache.py

Expected wall time: ~3-6 minutes (~530 Claude calls + ~540 Voyage embeddings).
"""

from __future__ import annotations

import pickle
import sys
import time
from pathlib import Path

# Add AI-3 repo root to sys.path so `pipeline.*` resolves whether this script
# is run as `python notebooks/scripts/build_embedding_cache.py` or otherwise.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import anthropic
import numpy as np
from dotenv import load_dotenv
from sklearn.decomposition import PCA

from pipeline.embeddings.embed import embed_texts
from pipeline.eval.golden_set import GOLDEN_SET
from pipeline.ingestion.store import get_collection

load_dotenv()

_client = anthropic.Anthropic()

CACHE_PATH = Path("notebooks/_cache/pca_viz_cache.pkl")
N_QUESTIONS_PER_CHUNK = 3


# ---------------------------------------------------------------------------
# HyDE: generate a hypothetical answer for retrieval embedding
# ---------------------------------------------------------------------------
def generate_hypothetical_answer(question: str, domain: str = "company") -> str:
    """Reference HyDE implementation (matches 1.1 lesson plan)."""
    response = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        system=(
            "Write as if this is an excerpt from an internal company document. "
            "Be specific. Do not hedge or say 'I don't know.'"
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Answer in 2-3 sentences as if you were an internal {domain} "
                f"document: {question}"
            ),
        }],
        temperature=0.0,
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Enrichment: generate N questions that a chunk answers (DR-012 correct form)
# ---------------------------------------------------------------------------
def generate_questions_for_chunk(chunk_text: str, n: int = N_QUESTIONS_PER_CHUNK) -> list[str]:
    """Ask Claude for N questions this chunk would answer."""
    response = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                f"Generate exactly {n} distinct questions that this text answers. "
                f"Output ONE question per line, no numbering, no extra text.\n\n"
                f"TEXT:\n{chunk_text}"
            ),
        }],
        temperature=0.0,
    )
    lines = [ln.strip() for ln in response.content[0].text.splitlines() if ln.strip()]
    return lines[:n]


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
# We pickle a plain dict (not a dataclass) so the notebook can unpickle without
# needing to import any custom class. Keys are documented here:
#
#   chunk_texts / chunk_sources   parallel list[str], length 173
#   query_ids / query_texts / query_expected_sources   parallel list, length 10
#   hyde_texts                    list[str] length 10 — hypothetical answers
#   enrich_questions              list[str] length 519
#   enrich_chunk_indices          list[int] length 519 — back-pointer 0..172
#   chunk_emb, query_emb, hyde_emb, enrich_emb   np.ndarray full-D for cosine
#   pca                           fitted sklearn PCA(n_components=3)
#   chunk_proj, query_proj, hyde_proj, enrich_proj   np.ndarray (N, 3)


def main() -> None:
    t0 = time.time()

    # --- Step 1: pull corpus chunks + embeddings from ChromaDB ---
    print("→ Loading corpus chunks from ChromaDB")
    col = get_collection()
    dump = col.get(include=["documents", "metadatas", "embeddings"])
    chunk_texts = dump["documents"]
    chunk_metas = dump["metadatas"]
    chunk_emb = np.array(dump["embeddings"])
    chunk_sources = [m.get("source", "unknown") for m in chunk_metas]
    print(f"  loaded {len(chunk_texts)} chunks, embedding dim = {chunk_emb.shape[1]}")

    # --- Step 2: embed the raw golden queries ---
    print("→ Embedding golden-set queries (raw)")
    query_texts = [q["question"] for q in GOLDEN_SET]
    query_ids = [q["id"] for q in GOLDEN_SET]
    query_expected_sources = [q["expected_source"] for q in GOLDEN_SET]
    query_emb = np.array(embed_texts(query_texts))
    print(f"  embedded {len(query_texts)} queries")

    # --- Step 3: HyDE hypothetical answers + their embeddings ---
    print("→ Generating HyDE hypothetical answers")
    hyde_texts = []
    for i, q in enumerate(query_texts):
        hyde_texts.append(generate_hypothetical_answer(q))
        print(f"  [{i+1}/{len(query_texts)}] {q[:60]}...")
    hyde_emb = np.array(embed_texts(hyde_texts))

    # --- Step 4: enrichment questions for every chunk ---
    print("→ Generating enrichment questions for every chunk (~3 min)")
    enrich_questions: list[str] = []
    enrich_chunk_indices: list[int] = []
    for idx, text in enumerate(chunk_texts):
        qs = generate_questions_for_chunk(text)
        enrich_questions.extend(qs)
        enrich_chunk_indices.extend([idx] * len(qs))
        if (idx + 1) % 20 == 0:
            print(f"  {idx+1}/{len(chunk_texts)} chunks done")

    print(f"→ Embedding {len(enrich_questions)} enrichment questions (in batches)")
    # embed_texts batches internally; just call it once on the full list
    enrich_emb = np.array(embed_texts(enrich_questions))

    # --- Step 5: fit PCA on the mixed dataset ---
    print("→ Fitting PCA(n=3) on mixed dataset")
    mixed = np.vstack([chunk_emb, query_emb, hyde_emb, enrich_emb])
    print(f"  mixed matrix shape: {mixed.shape}")
    pca = PCA(n_components=3)
    pca.fit(mixed)
    print(f"  explained variance per axis: {pca.explained_variance_ratio_}")

    # --- Step 6: project each category to 3D ---
    chunk_proj = pca.transform(chunk_emb)
    query_proj = pca.transform(query_emb)
    hyde_proj = pca.transform(hyde_emb)
    enrich_proj = pca.transform(enrich_emb)

    # --- Step 7: pickle everything ---
    bundle = {
        "chunk_texts": list(chunk_texts),
        "chunk_sources": chunk_sources,
        "query_ids": query_ids,
        "query_texts": query_texts,
        "query_expected_sources": query_expected_sources,
        "hyde_texts": hyde_texts,
        "enrich_questions": enrich_questions,
        "enrich_chunk_indices": enrich_chunk_indices,
        "chunk_emb": chunk_emb,
        "query_emb": query_emb,
        "hyde_emb": hyde_emb,
        "enrich_emb": enrich_emb,
        "pca": pca,
        "chunk_proj": chunk_proj,
        "query_proj": query_proj,
        "hyde_proj": hyde_proj,
        "enrich_proj": enrich_proj,
    }

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("wb") as f:
        pickle.dump(bundle, f)

    elapsed = time.time() - t0
    print(f"\n✓ Cache written to {CACHE_PATH} ({CACHE_PATH.stat().st_size / 1024:.1f} KB)")
    print(f"  Total wall time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
