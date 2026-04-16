"""
push_golden_set.py -- Upload the golden set to Phoenix Cloud as a dataset.

Run this ONCE per student workspace. After it succeeds, the dataset is visible
in the Phoenix UI under Datasets → `northbrook_golden_v1` and can be reused
across every experiment we run.

Usage:
    python scripts/push_golden_set.py

Requires:
    .env with PHOENIX_API_KEY, PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME

What this script does:
    1. Build three parallel lists from our golden set:
         - inputs:   the model-facing query  [{"question": "..."}]
         - outputs:  the ground truth        [{"expected_answer": "...", "expected_source": [...]}]
         - metadata: static info for filtering [{"id": "...", "category": "...", "difficulty": "..."}]
    2. Call client.datasets.create_dataset() to push all three as a single dataset.
    3. Phoenix returns a Dataset object; we print its name and link to the UI.

If you re-run this after editing golden_set.py, Phoenix will create a NEW
VERSION of the dataset with the same name. Existing experiments continue
pointing at the version they ran against.
"""

from dotenv import load_dotenv
from phoenix.client import Client

from pipeline.eval.golden_set import GOLDEN_SET, get_dataset_name

load_dotenv()

# Namespaced by PHOENIX_PROJECT_NAME so classmates sharing a workspace don't
# collide on the dataset name. See get_dataset_name() for details.
DATASET_NAME = get_dataset_name()


# Parallel lists — Phoenix keys them together by list index.
# inputs[i] pairs with outputs[i] and metadata[i].

inputs = [
    {"question": q["question"]}
    for q in GOLDEN_SET
]

outputs = [
    {
        "expected_answer": q["expected_answer"],
        "expected_source": q["expected_source"],
    }
    for q in GOLDEN_SET
]

metadata = [
    {
        "id": q["id"],
        "category": q["category"],
        "difficulty": q["difficulty"],
    }
    for q in GOLDEN_SET
]


def main() -> None:
    client = Client()

    print(f"→ Pushing golden set as dataset: {DATASET_NAME}")
    dataset = client.datasets.create_dataset(
        name=DATASET_NAME,
        dataset_description=(
            "Seed golden set for AI-3 RAG evaluation. 10 queries across "
            "policy_lookup, multi_doc, compound, and procedural categories. "
            "Students grow this in Lab 2 with adversarial and feedback-derived cases."
        ),
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
    )

    print(f"✓ Uploaded {len(GOLDEN_SET)} queries as: {DATASET_NAME}")
    print(f"  View at: https://app.phoenix.arize.com")
    print(f"  Navigate to: Datasets → {DATASET_NAME}")


if __name__ == "__main__":
    main()
