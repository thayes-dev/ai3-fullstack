"""
enriched.py -- Question Enrichment at Ingestion Time

At ingestion time, generate questions each chunk answers.
Embed those questions alongside the chunk for better query matching.

This closes the embedding gap from the other direction: instead of making
queries sound like answers (HyDE), we make the index include question-like
text so queries match naturally.

Session 1.1: We build these functions together in class.
"""

import chromadb
import anthropic
from pathlib import Path

from pipeline.embeddings.embed import embed_texts
from pipeline.ingestion.store import get_collection, CHROMA_PATH

client = anthropic.Anthropic()

ENRICHED_COLLECTION = "northbrook_enriched"


# We'll build generate_questions_for_chunk(), enrich_and_store(),
# and enriched_retrieve() together in class
