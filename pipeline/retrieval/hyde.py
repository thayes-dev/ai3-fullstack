"""
hyde.py -- Hypothetical Document Embeddings

Transform queries by generating hypothetical answers, then embed the
hypothetical answer for retrieval instead of the raw question.

This closes the embedding gap: questions and answers live in different
neighborhoods. By generating a hypothetical answer, we move our search
vector into "answer space" where the real answers live.

Session 1.1: We build these functions together in class.
"""

import anthropic
from pipeline.embeddings.embed import embed_texts
from pipeline.ingestion.store import get_collection

client = anthropic.Anthropic()


def generate_hypothetical_answer(question: str, domain: str = "company") -> str:
    """Generate a hypothetical answer for embedding-based retrieval.

    The answer does NOT need to be correct. It needs to SOUND like
    the kind of document that contains the real answer.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"Answer this question in 2-3 sentences as if you were an internal {domain} document: {question}"
        }],
        system=(
            "You are generating a hypothetical document passage for embedding-based retrieval. "
            "Write as if this is an excerpt from an internal company document. "
            "Be specific and use professional language. "
            "Do not hedge or say 'I don't know.' Write a direct, factual-sounding passage."
        )
    )
    return response.content[0].text

def hyde_retrieve(question: str, n_results: int = 5, domain: str = "company") -> list[dict]:
    """Retrieve using HyDE: embed a hypothetical answer instead of the question."""
    # Step 1: Generate hypothetical answer
    hypothetical = generate_hypothetical_answer(question, domain)

    # Step 2: Embed the hypothetical answer (NOT the question!)
    hyde_embedding = embed_texts([hypothetical])[0]

    # Step 3: Search ChromaDB with the hypothetical answer embedding
    collection = get_collection()
    results = collection.query(
        query_embeddings=[hyde_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # Step 4: Format results
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "metadata": meta,
            "score": 1 - dist,
            "hyde_answer": hypothetical
        })
    return chunks
