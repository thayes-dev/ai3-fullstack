"""
Quick Smoke Test — Verify project setup (FREE, no API calls).

Run: uv run python scripts/check.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

errors = []
warnings = []


def check(label, fn):
    try:
        fn()
        print(f"  [OK] {label}")
    except Exception as e:
        errors.append(f"{label}: {e}")
        print(f"  [FAIL] {label}: {e}")


def warn(label, fn):
    try:
        fn()
        print(f"  [OK] {label}")
    except Exception:
        warnings.append(label)
        print(f"  [WARN] {label}")


print("=" * 50)
print("Project Smoke Test")
print("=" * 50)

# 1. Environment
print("\n--- Environment ---")
check(".env file exists", lambda: (ROOT / ".env").stat())
check("student_config.yaml exists", lambda: (ROOT / "student_config.yaml").stat())

# 2. Core imports
print("\n--- Core Imports ---")
check("import anthropic", lambda: __import__("anthropic"))
check("import streamlit", lambda: __import__("streamlit"))
check("import chromadb", lambda: __import__("chromadb"))
check("import voyageai", lambda: __import__("voyageai"))

# 3. Pipeline imports
print("\n--- Pipeline Imports ---")
check("pipeline.generation.generate", lambda: __import__("pipeline.generation.generate", fromlist=["call_claude"]))
check("pipeline.embeddings.embed", lambda: __import__("pipeline.embeddings.embed", fromlist=["get_embedding"]))
check("pipeline.retrieval.naive", lambda: __import__("pipeline.retrieval.naive", fromlist=["naive_retrieve"]))
check("pipeline.context.assembler", lambda: __import__("pipeline.context.assembler", fromlist=["contextualize_query"]))
check("pipeline.context.manager", lambda: __import__("pipeline.context.manager", fromlist=["manage_history"]))
check("pipeline.safety.guard", lambda: __import__("pipeline.safety.guard", fromlist=["validate_input"]))

# 4. App imports
print("\n--- App Imports ---")
check("app.rag", lambda: __import__("app.rag", fromlist=["get_response"]))
check("app.branding", lambda: __import__("app.branding", fromlist=["apply_branding"]))
warn("app.feedback", lambda: __import__("app.feedback", fromlist=["submit_feedback"]))

# 5. API keys (check presence, not validity)
print("\n--- API Keys ---")
from dotenv import load_dotenv
import os
load_dotenv(ROOT / ".env")
check("ANTHROPIC_API_KEY set", lambda: None if os.getenv("ANTHROPIC_API_KEY") else (_ for _ in ()).throw(ValueError("Not set")))
check("VOYAGE_API_KEY set", lambda: None if os.getenv("VOYAGE_API_KEY") else (_ for _ in ()).throw(ValueError("Not set")))

# Summary
print("\n" + "=" * 50)
if errors:
    print(f"FAIL: {len(errors)} error(s)")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
elif warnings:
    print(f"PASS with {len(warnings)} warning(s)")
    sys.exit(0)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
