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


# We'll build generate_questions_for_chunk(), enrich_and_store(),
# and enriched_retrieve() together in class
