"""
run_experiment.py -- Run retrieval strategy comparison as Phoenix experiments.

Lab 2: three strategies compared -- naive, hyde, and rrf.

Usage:
    uv run python scripts/run_experiment.py            # golden set
    uv run python scripts/run_experiment.py --safety   # adversarial set

Requires:
    - .env with PHOENIX_API_KEY, ANTHROPIC_API_KEY, VOYAGE_API_KEY
    - Golden set already pushed (run scripts/push_golden_set.py first)
    - Enriched collection seeded (required for rrf_task -- see rrf.py)

What to look for in Phoenix:
    - Datasets -> northbrook_golden_v1 -> Experiments tab
    - Compare retrieval_hit and answer_addresses_question across all three
    - Multi-doc queries (office_relocation, ceo_priorities) show RRF's
      biggest gains over naive
"""

import argparse

from dotenv import load_dotenv
from phoenix.client import Client

from pipeline.eval.golden_set import get_dataset_name
from pipeline.eval.tasks import naive_task, hyde_task, rrf_task
from pipeline.eval.evaluators import retrieval_hit, answer_addresses_question

load_dotenv()

DATASET_NAME = get_dataset_name()
ADVERSARIAL_DATASET_NAME = get_dataset_name(base="northbrook_adversarial_v1")

MODEL_NAME = "claude-sonnet-4-5"

EVALUATORS = [
    retrieval_hit,
    answer_addresses_question,
]

# Lab 2: added rrf_task as the primary strategy being evaluated.
PIPELINES = [
    ("naive", naive_task),
    ("hyde", hyde_task),
    ("rrf", rrf_task),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phoenix retrieval experiments")
    parser.add_argument(
        "--safety",
        action="store_true",
        help="Run against the adversarial dataset instead of the golden set",
    )
    args = parser.parse_args()

    client = Client()

    if args.safety:
        dataset_name = ADVERSARIAL_DATASET_NAME
        dataset_label = "adversarial"
    else:
        dataset_name = DATASET_NAME
        dataset_label = "golden"

    print(f"-> Using dataset: {dataset_name} ({dataset_label})")
    dataset = client.datasets.get_dataset(dataset=dataset_name)

    for label, task_fn in PIPELINES:
        experiment_name = f"{label} / {MODEL_NAME} / {dataset_label}"
        print(f"\n>> Running experiment: {experiment_name}")

        client.experiments.run_experiment(
            dataset=dataset,
            task=task_fn,
            evaluators=EVALUATORS,
            experiment_name=experiment_name,
            experiment_metadata={
                "pipeline": label,
                "model": MODEL_NAME,
                "dataset": dataset_label,
            },
        )

        print(f"  Done.")

    print("\nAll experiments complete.")
    print("  Compare results at: https://app.phoenix.arize.com")
    print(f"  Datasets -> {dataset_name} -> Experiments tab")


if __name__ == "__main__":
    main()
