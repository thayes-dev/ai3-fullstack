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
    """Generate a HyDE-style hypothetical answer for retrieval.

    The hypothetical answer does not need to be factually correct. It
    needs to sound like an excerpt from a policy document or handbook so
    the embedding lands in answer space rather than question space.

    Args:
        question: The user's original question.
        domain: Hint for what kind of document to mimic.

    Returns:
        A brief hypothetical answer passage.
    """
    system_prompt = (
        f"You are writing an excerpt from an internal {domain} policy document or handbook. "
        "Write a brief passage (2-3 sentences) that answers the following question as if it were from such a document. "
        "Make it sound like official, professional documentation. Do not include the question in your response."
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        temperature=0.7,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )

    return response.content[0].text.strip()


def hyde_retrieve(question: str, n_results: int = 5, domain: str = "company") -> list[dict]:
    """Retrieve chunks by embedding a hypothetical answer instead of the question.

    Args:
        question: The user's original question.
        n_results: Number of chunks to retrieve.
        domain: Hint for the hypothetical answer generation.

    Returns:
        A list of dicts with keys: text, metadata, score, hyde_answer.
    """
    collection = get_collection()

    hypothetical_answer = generate_hypothetical_answer(question, domain=domain)
    query_embedding = embed_texts([hypothetical_answer])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    sources = [
        {
            "text": doc,
            "metadata": meta,
            "score": 1 - dist,
            "hyde_answer": hypothetical_answer,
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

    sources.sort(key=lambda item: item["score"], reverse=True)
    return sources
