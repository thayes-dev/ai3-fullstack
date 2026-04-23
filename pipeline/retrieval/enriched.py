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
from pipeline.ingestion.store import CHROMA_PATH

client = anthropic.Anthropic()

ENRICHED_COLLECTION = "northbrook_enriched"
N_QUESTIONS_PER_CHUNK = 3


def _get_enriched_collection(collection_name: str = ENRICHED_COLLECTION) -> chromadb.Collection:
    """Get or create the enriched ChromaDB collection."""
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    return db.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def generate_questions_for_chunk(chunk_text: str, n_questions: int = N_QUESTIONS_PER_CHUNK) -> list[str]:
    """Ask Claude for questions that this chunk would answer."""
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate exactly {n_questions} distinct questions that this text answers. "
                    "Output ONE question per line, no numbering, no extra text.\n\n"
                    f"TEXT:\n{chunk_text}"
                ),
            }
        ],
        temperature=0.0,
    )

    lines = [line.strip() for line in response.content[0].text.splitlines() if line.strip()]
    return lines[:n_questions]


def enrich_and_store(chunks: list[dict], collection_name: str = ENRICHED_COLLECTION) -> None:
    """Process chunks with enrichment and store them in ChromaDB."""
    db = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        db.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = db.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    all_questions: list[str] = []
    all_documents: list[str] = []
    all_metadatas: list[dict] = []
    all_ids: list[str] = []

    for chunk in chunks:
        chunk_text = chunk["text"]
        metadata = chunk["metadata"].copy()
        chunk_source = metadata.get("source", "unknown")
        chunk_index = metadata.get("chunk_index", 0)

        questions = generate_questions_for_chunk(chunk_text, n_questions=N_QUESTIONS_PER_CHUNK)

        for question_index, question in enumerate(questions):
            row_id = f"{chunk_source}_chunk{chunk_index}_q{question_index}"
            row_metadata = {
                **metadata,
                "chunk_index": chunk_index,
                "source_question": question,
            }

            all_ids.append(row_id)
            all_documents.append(chunk_text)
            all_questions.append(question)
            all_metadatas.append(row_metadata)

    embeddings = embed_texts(all_questions)

    collection.add(
        ids=all_ids,
        documents=all_documents,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )


def enriched_retrieve(
    question: str,
    n_results: int = 5,
    collection_name: str = ENRICHED_COLLECTION,
) -> list[dict]:
    """Retrieve from the enriched collection with top-N deduped chunks."""
    collection = _get_enriched_collection(collection_name)

    query_embedding = embed_texts([question])[0]
    over_fetch = n_results * N_QUESTIONS_PER_CHUNK

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=over_fetch,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    best_per_chunk: dict[int, dict] = {}
    for doc, metadata, distance in zip(documents, metadatas, distances):
        chunk_index = metadata.get("chunk_index")
        if chunk_index is None:
            continue

        score = 1 - distance
        existing = best_per_chunk.get(chunk_index)
        if existing is None or score > existing["score"]:
            best_per_chunk[chunk_index] = {
                "text": doc,
                "metadata": metadata,
                "score": score,
                "matched_question": metadata.get("source_question"),
            }

    sorted_results = sorted(best_per_chunk.values(), key=lambda item: item["score"], reverse=True)
    return sorted_results[:n_results]
