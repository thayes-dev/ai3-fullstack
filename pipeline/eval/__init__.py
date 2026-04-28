"""
pipeline.eval -- Evaluation layer for the RAG pipeline.

This package contains:
    golden_set       -- The curated correctness test set (Session 1.2)
    adversarial_set  -- The "Black Hat" safety test set (Session 3.1)
    tasks            -- Task closures: naive_task, hyde_task, safety_task
    evaluators       -- Pass/fail functions: retrieval_hit, answer_addresses_question, safety_check

Students build evaluators live in Session 1.2 (correctness) and Session 3.1
(safety); the rest is provided.
"""
