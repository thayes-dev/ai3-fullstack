"""
enriched.py -- Question Enrichment at Ingestion Time

At ingestion time, generate questions each chunk answers.
Embed EACH question as its own row in the vector store, with the
original chunk text as the 'documents' field.

This closes the embedding gap from the other direction: queries match
question embeddings directly (pure question-space), and we return the
chunk that the matched question points to.

Session 1.1: We build these functions together in class.
"""

import chromadb
import anthropic

from pipeline.embeddings.embed import embed_texts
from pipeline.ingestion.store import get_collection, CHROMA_PATH

client = anthropic.Anthropic()

ENRICHED_COLLECTION = "northbrook_enriched"
N_QUESTIONS_PER_CHUNK = 3


def generate_questions_for_chunk(chunk_text: str, n_questions: int = N_QUESTIONS_PER_CHUNK) -> list[str]:
    """Generate questions that this chunk answers."""
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        temperature=0,
        messages=[{
            "role": "user",
            "content": (
                f"What {n_questions} questions does this text passage answer? "
                f"Return only the questions, one per line. No numbering, no extra text.\n\n"
                f"Passage: {chunk_text}"
            )
        }]
    )
    raw = response.content[0].text.strip().split("\n")
    return [q.strip() for q in raw if q.strip()]

def enrich_and_store(chunks: list[dict], collection_name: str = ENRICHED_COLLECTION) -> None:
    """Process chunks with enrichment and store in ChromaDB."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Delete if exists for clean re-enrichment
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    total_rows = 0
    for chunk_idx, chunk in enumerate(chunks):
        print(f"  Chunk {chunk_idx+1}/{len(chunks)}...")
        questions = generate_questions_for_chunk(chunk["text"])
        if not questions:
            continue
        
        # Batch: embed all N questions in one Voyage call
        embeddings = embed_texts(questions)
        source = chunk["metadata"].get("source", "unknown")
        
        # One row per question — same chunk text, different embedding
        for q_idx, (question, embedding) in enumerate(zip(questions, embeddings)):
            meta = dict(chunk["metadata"])
            meta["chunk_index"] = chunk_idx
            meta["source_question"] = question
            
            collection.add(
                ids=[f"{source}_chunk{chunk_idx}_q{q_idx}"],
                documents=[chunk["text"]],     # What we return on retrieval
                embeddings=[embedding],         # Pure question-space vector
                metadatas=[meta]
            )
            total_rows += 1
    
    print(f"  Stored {len(chunks)} chunks × {N_QUESTIONS_PER_CHUNK} questions = {total_rows} rows")

def enriched_retrieve(question: str, n_results: int = 5, collection_name: str = ENRICHED_COLLECTION) -> list[dict]:
    """Retrieve from the enriched collection (dedup to unique chunks)."""
    question_embedding = embed_texts([question])[0]
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(name=collection_name)
    
    # Over-fetch: multiple questions per chunk may match, we need headroom to dedup
    raw = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results * N_QUESTIONS_PER_CHUNK,
        include=["documents", "metadatas", "distances"]
    )
    
    # Dedup by chunk_index, keep best score per chunk
    seen = {}
    for doc, meta, dist in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        chunk_id = meta.get("chunk_index")
        if chunk_id is None:
            continue  # defensive: skip rows without chunk_index
        score = 1 - dist
        if chunk_id not in seen or score > seen[chunk_id]["score"]:
            seen[chunk_id] = {
                "text": doc,
                "metadata": meta,
                "score": score,
                "matched_question": meta.get("source_question"),
            }
    
    unique = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    if len(unique) < n_results:
        print(f"  Note: {len(unique)} unique chunks returned (requested {n_results})")
    return unique[:n_results]
