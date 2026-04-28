"""
push_golden_set.py -- Upload (or sync) the golden set to Phoenix Cloud.

This script is idempotent — safe to re-run after editing golden_set.py:

    1. If the dataset doesn't exist, create it from the full GOLDEN_SET.
    2. If it exists, diff by metadata.id and APPEND only the entries
       Phoenix doesn't already have. Phoenix tracks the append as a
       new dataset version; existing experiments stay pinned to the
       version they ran against.

Each row carries a `history` field in its inputs (empty list for single-turn
cases, populated for multi-turn cases). This is required by the Session 2.2
context-management experiments (rewrite_only, assemble_only, rewrite_and_assemble)
in pipeline/eval/tasks.py.

Usage:
    python scripts/push_golden_set.py

Requires:
    .env with PHOENIX_API_KEY, PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME

Note on history-field updates: append-only means edits to EXISTING rows
(e.g., changing the wording of question 3) won't propagate. To reset, delete
the dataset in the Phoenix UI and re-run this script.
"""

from dotenv import load_dotenv
import httpx
from phoenix.client import Client

from pipeline.eval.golden_set import GOLDEN_SET, get_dataset_name

load_dotenv()

# Namespaced by PHOENIX_PROJECT_NAME so classmates sharing a workspace don't
# collide on the dataset name. See get_dataset_name() for details.
DATASET_NAME = get_dataset_name()


def _row_to_input(q: dict) -> dict:
    return {"question": q["question"], "history": q.get("history", [])}


def _row_to_output(q: dict) -> dict:
    return {
        "expected_answer": q["expected_answer"],
        "expected_source": q["expected_source"],
    }


def _row_to_metadata(q: dict) -> dict:
    return {
        "id": q["id"],
        "category": q["category"],
        "difficulty": q["difficulty"],
    }


def _create_full(client: Client) -> None:
    print(f"→ Creating dataset {DATASET_NAME} with {len(GOLDEN_SET)} rows")
    client.datasets.create_dataset(
        name=DATASET_NAME,
        dataset_description=(
            "Golden set for AI-3 RAG evaluation. 15 queries across "
            "policy_lookup, multi_doc, compound, procedural, and multi_turn "
            "categories. The 5 multi_turn cases include prior conversation "
            "`history` so contextualize_query has signal to move. Students "
            "grow this in Lab 2 with adversarial and feedback-derived cases."
        ),
        inputs=[_row_to_input(q) for q in GOLDEN_SET],
        outputs=[_row_to_output(q) for q in GOLDEN_SET],
        metadata=[_row_to_metadata(q) for q in GOLDEN_SET],
    )
    print(f"✓ Created with {len(GOLDEN_SET)} rows")


def _sync_missing(client: Client) -> None:
    """Append rows from GOLDEN_SET whose metadata.id isn't already in Phoenix."""
    existing = client.datasets.get_dataset(dataset=DATASET_NAME)
    existing_ids = {ex["metadata"]["id"] for ex in existing.examples}
    print(f"→ Dataset exists with {len(existing_ids)} rows: {sorted(existing_ids)}")

    missing = [q for q in GOLDEN_SET if q["id"] not in existing_ids]
    if not missing:
        print("✓ Already in sync — nothing to append")
        return

    print(f"→ Appending {len(missing)} new rows: {[q['id'] for q in missing]}")
    client.datasets.add_examples_to_dataset(
        dataset=DATASET_NAME,
        inputs=[_row_to_input(q) for q in missing],
        outputs=[_row_to_output(q) for q in missing],
        metadata=[_row_to_metadata(q) for q in missing],
    )
    print(f"✓ Appended {len(missing)} rows")


def main() -> None:
    client = Client()
    print(f"→ Target dataset: {DATASET_NAME}")
    try:
        _create_full(client)
    except Exception as e:
        # Phoenix returns 409 Conflict when the dataset already exists.
        # The client wraps it in DatasetUploadError but we sniff for the
        # underlying status and fall through to the append path.
        is_conflict = (
            isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 409
        ) or "already exists" in str(e).lower()
        if not is_conflict:
            raise
        print(f"  (dataset exists — switching to sync mode)")
        _sync_missing(client)

    print(f"\n  View at: https://app.phoenix.arize.com")
    print(f"  Datasets → {DATASET_NAME}")


if __name__ == "__main__":
    main()
