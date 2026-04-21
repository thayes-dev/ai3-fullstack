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


# We'll build generate_hypothetical_answer() and hyde_retrieve() together in class
