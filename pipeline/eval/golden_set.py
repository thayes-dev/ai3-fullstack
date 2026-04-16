"""
golden_set.py -- The curated 10-query test set for AI-3 Session 1.2 evaluation.

This set was validated against the Northbrook corpus during the Session 1.1
enrichment correctness fix (see decisions/012-enrichment-correctness-fix.md).
It is the seed the class starts with. Students will grow it in Lab 2 by
adding adversarial queries, feedback-derived cases, and out-of-scope checks.

Structure of each entry:
    id               -- Short stable identifier, snake_case
    question         -- The query string (verbatim from student-facing materials)
    expected_answer  -- Ground-truth canonical answer, corpus-grounded, 1-2 sentences
    expected_source  -- List of source filenames that should be retrieved
                        (multi-doc queries may list several)
    category         -- policy_lookup | multi_doc | compound | procedural | out_of_scope
    difficulty       -- easy | medium | hard

The `expected_answer` strings are short and declarative — they mirror how the
source documents write the information. An LLM judge compares the generated
answer against these strings (see pipeline/eval/evaluators.py).

To explore: print `len(GOLDEN_SET)`, inspect `[q["category"] for q in GOLDEN_SET]`,
or filter by difficulty: `[q for q in GOLDEN_SET if q["difficulty"] == "easy"]`.
"""


GOLDEN_SET = [
    # 1. Single-topic lookup in vacation_policy_2025.md (HyDE winner in 1.1)
    {
        "id": "vacation_policy",
        "question": "What is the vacation policy?",
        "expected_answer": (
            "Eligible full-time employees receive 20 vacation days per calendar "
            "year, with up to 10 days allowed to carry over. Requests require at "
            "least two weeks' advance notice, or 30 days for five or more "
            "consecutive days."
        ),
        "expected_source": ["vacation_policy_2025.md"],
        "category": "policy_lookup",
        "difficulty": "easy",
    },

    # 2. Single-topic lookup in expense_policy.md (HyDE winner in 1.1)
    {
        "id": "expense_reimbursement",
        "question": "What are the expense reimbursement rules?",
        "expected_answer": (
            "Expenses must be business-related and submitted within 30 days with "
            "itemized receipts. Meals are capped at $65 per day for travel and "
            "$50 per person for team meals. Reimbursements are processed bi-weekly "
            "aligned with payroll."
        ),
        "expected_source": ["expense_policy.md"],
        "category": "policy_lookup",
        "difficulty": "easy",
    },

    # 3. Enumeration from single policy doc (HyDE winner in 1.1)
    {
        "id": "pto_types",
        "question": "What are the three main types of paid time off Northbrook offers?",
        "expected_answer": (
            "The three main types are vacation days (20 per year), unlimited "
            "sick days, and personal days (3 per year). Northbrook also offers "
            "Recharge Days (2 per year) as a new 2025 benefit."
        ),
        "expected_source": ["vacation_policy_2025.md"],
        "category": "policy_lookup",
        "difficulty": "easy",
    },

    # 4. Multi-topic single doc (enrichment winner: Q4 board meeting)
    {
        "id": "q4_board_meeting",
        "question": "What happened at the Q4 board meeting?",
        "expected_answer": (
            "The board reviewed strong Q4 financials ($14.1M revenue, $2.9M net "
            "income), approved a $2.1M AI initiative called Project Meridian, "
            "and confirmed the office relocation to 250 Innovation Drive for "
            "March 2025."
        ),
        "expected_source": ["board_meeting_q4_2024.md"],
        "category": "multi_doc",
        "difficulty": "medium",
    },

    # 5. Cross-document synthesis (enrichment winner: office move across 3 docs)
    {
        "id": "office_relocation",
        "question": "What was discussed about office relocation?",
        "expected_answer": (
            "Northbrook is relocating from 100 Main Street to 250 Innovation "
            "Drive in March 2025. The new 45,000-square-foot space includes 60 "
            "private focus rooms, a café, 180 parking spaces, and an event space. "
            "The current office no longer accommodates the 320-person workforce."
        ),
        "expected_source": [
            "memo_office_relocation.md",
            "board_meeting_q3_2024.md",
            "board_meeting_q4_2024.md",
        ],
        "category": "multi_doc",
        "difficulty": "medium",
    },

    # 6. Multi-part / compound question (enrichment winner: timeline + prep)
    {
        "id": "office_move_timeline",
        "question": "What's the timeline for the office move and what do I need to do to prepare?",
        "expected_answer": (
            "The move happens March 1-2, 2025. Prepare by packing personal items "
            "the week of Feb 10, receiving your desk assignment by Feb 7, "
            "cleaning shared spaces by Feb 21, and updating your address in the "
            "HR portal by March 1. Do not pack IT equipment; IT handles all "
            "technology setup."
        ),
        "expected_source": ["memo_office_relocation.md"],
        "category": "compound",
        "difficulty": "medium",
    },

    # 7. Two-part compound across docs (enrichment winner: CEO + priorities)
    {
        "id": "ceo_priorities",
        "question": "Who is the CEO and what are their priorities?",
        "expected_answer": (
            "Sarah Chen is the CEO. Her 2025 priorities are AI-First Services "
            "(Project Meridian, $2.1M investment), market expansion into Seattle, "
            "Atlanta, and Boston, and a $60M revenue target representing 23% growth."
        ),
        "expected_source": ["memo_ceo_annual_kickoff.md"],
        "category": "compound",
        "difficulty": "medium",
    },

    # 8. Procedural / how-to (enrichment winner)
    {
        "id": "vpn_setup",
        "question": "How do I set up VPN access?",
        "expected_answer": (
            "Download the new Cloudflare Zero Trust VPN client from the IT "
            "self-service portal (available Jan 27). It replaces SecureLink and "
            "offers faster speeds and MFA integration. Company laptops deploy "
            "automatically; personal devices require manual install per IT's "
            "support page."
        ),
        "expected_source": ["memo_security_update.md"],
        "category": "procedural",
        "difficulty": "easy",
    },

    # 9. Policy lookup (enrichment winner: performance review)
    {
        "id": "performance_review",
        "question": "What are the performance review procedures?",
        "expected_answer": (
            "Northbrook conducts quarterly performance reviews run by direct "
            "managers using a rubric covering quality of work, collaboration, "
            "client satisfaction, initiative, and values alignment. Mid-year and "
            "year-end reviews include self-assessments and peer feedback. "
            "Compensation adjustments happen in the December year-end cycle."
        ),
        "expected_source": ["employee_handbook.md"],
        "category": "policy_lookup",
        "difficulty": "medium",
    },

    # 10. Policy lookup (enrichment winner: remote work)
    {
        "id": "remote_work",
        "question": "How does the company handle remote work requests?",
        "expected_answer": (
            "Northbrook operates a hybrid model: eligible full-time employees "
            "work 3 days in-office (Tuesday, Wednesday, Thursday) and 2 days "
            "remotely. Fully remote arrangements require VP-level approval and "
            "are limited to regions without a Northbrook office. Remote workers "
            "receive a $1,500 equipment stipend and must use the company VPN."
        ),
        "expected_source": ["remote_work_policy.md"],
        "category": "policy_lookup",
        "difficulty": "easy",
    },
]


# Quick sanity checks — also useful for students to explore
assert len(GOLDEN_SET) == 10, "Golden set must have exactly 10 queries"
assert all("expected_answer" in q for q in GOLDEN_SET), "Every query needs an expected answer"
assert all(isinstance(q["expected_source"], list) for q in GOLDEN_SET), \
    "expected_source must be a list (even if it has one element)"
