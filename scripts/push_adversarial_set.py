"""
push_adversarial_set.py -- Upload the adversarial "Black Hat" set to Phoenix.

Run this after Session 3.1 to create the safety evaluation dataset.
Students can extend it by creating pipeline/eval/student_attacks.py with
a STUDENT_ATTACKS list following the same schema.

Usage:
    python scripts/push_adversarial_set.py
    python scripts/push_adversarial_set.py --include-student

Requires:
    .env with PHOENIX_API_KEY, PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME
"""

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from phoenix.client import Client

from pipeline.eval.adversarial_set import ADVERSARIAL_SET, get_dataset_name

load_dotenv()

DATASET_NAME = get_dataset_name(base="northbrook_adversarial_v1")


def load_attacks(include_student: bool) -> list[dict]:
    """Load base attacks and optionally merge student additions."""
    attacks = list(ADVERSARIAL_SET)

    if include_student:
        try:
            mod = importlib.import_module("pipeline.eval.student_attacks")
            student = getattr(mod, "STUDENT_ATTACKS", [])
            # Check for duplicate IDs
            base_ids = {a["id"] for a in attacks}
            for sa in student:
                if sa["id"] in base_ids:
                    print(f"  ⚠ Skipping duplicate ID: {sa['id']}")
                else:
                    attacks.append(sa)
            print(f"  + Added {len(student)} student attacks")
        except ImportError:
            print("  ℹ No student_attacks.py found — using base set only")

    return attacks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-student", action="store_true",
                        help="Include student_attacks.py if it exists")
    args = parser.parse_args()

    attacks = load_attacks(args.include_student)

    inputs = [{"question": a["question"]} for a in attacks]
    outputs = [{"expected_behavior": a["expected_behavior"]} for a in attacks]
    metadata = [
        {
            "id": a["id"],
            "attack_type": a["attack_type"],
            "severity": a["severity"],
            "description": a["description"],
        }
        for a in attacks
    ]

    client = Client()
    print(f"→ Pushing adversarial set as dataset: {DATASET_NAME}")

    client.datasets.create_dataset(
        name=DATASET_NAME,
        dataset_description=(
            "Black Hat adversarial test set for AI-3 safety evaluation. "
            f"{len(attacks)} attack cases across 6 categories. "
            "Students extend this in Lab 2 with additional attack patterns."
        ),
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
    )

    # Print attack type breakdown
    from collections import Counter
    type_counts = Counter(a["attack_type"] for a in attacks)
    print(f"✓ Uploaded {len(attacks)} attacks as: {DATASET_NAME}")
    print(f"  Breakdown:")
    for atype, count in sorted(type_counts.items()):
        print(f"    {atype}: {count}")


if __name__ == "__main__":
    main()
