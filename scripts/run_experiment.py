"""
run_experiment.py -- Run the naive-vs-HyDE comparison as two Phoenix experiments.

This is the payoff script. For each retrieval strategy:
    1. Fetch the golden-set dataset we uploaded earlier
    2. Run every query through the strategy's task
    3. Grade each output with both evaluators (retrieval_hit + answer_addresses_question)
    4. Phoenix logs results to the UI as a side-by-side comparison table

Usage:
    python scripts/run_experiment.py

Requires:
    - .env with PHOENIX_API_KEY, ANTHROPIC_API_KEY, VOYAGE_API_KEY
    - Golden set already pushed (run scripts/push_golden_set.py first)
    - pipeline/eval/evaluators.py filled in (the two functions have bodies)

What to look for in the Phoenix UI after this finishes:
    - Open your dataset → Experiments tab
    - You should see two experiments: "naive / ..." and "hyde / ..."
    - Open one and inspect the per-row scores for each evaluator
    - Compare the aggregate pass rates — does HyDE actually help?
"""

from dotenv import load_dotenv
from phoenix.client import Client

from pipeline.eval.tasks import naive_task, hyde_task
from pipeline.eval.evaluators import retrieval_hit, answer_addresses_question

load_dotenv()


# The model students are running against — used in experiment naming so
# results stay traceable if you swap models later.
MODEL_NAME = "claude-sonnet-4-5"

# Evaluators are a list. Phoenix uses each function's __name__ as the
# column label in the UI. Keep function names descriptive.
EVALUATORS = [
    retrieval_hit,
    answer_addresses_question,
]

# Each entry is (experiment_label, task_function). We run one experiment
# per pipeline so the comparison lives natively in Phoenix.
PIPELINES = [
    ("naive", naive_task),
    ("hyde", hyde_task),
]


def main() -> None:
    client = Client()

    # Fetch the dataset we uploaded with push_golden_set.py
    dataset = client.datasets.get_dataset(dataset="northbrook_golden_v1")

    for label, task_fn in PIPELINES:
        experiment_name = f"{label} / {MODEL_NAME}"
        print(f"\n▸ Running experiment: {experiment_name}")

        experiment = client.experiments.run_experiment(
            dataset=dataset,
            task=task_fn,
            evaluators=EVALUATORS,
            experiment_name=experiment_name,
            experiment_metadata={
                "pipeline": label,
                "model": MODEL_NAME,
            },
        )

        print(f"  ✓ Experiment complete")

    print("\n✓ All experiments done")
    print("  Compare results at: https://app.phoenix.arize.com")
    print("  Datasets → northbrook_golden_v1 → Experiments tab")


if __name__ == "__main__":
    main()
