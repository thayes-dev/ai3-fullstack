"""INSTRUCTOR LOCAL — populated solutions for testing. Not committed."""
from typing import Literal
import anthropic
from pydantic import BaseModel, Field

_client = anthropic.Anthropic()


def retrieval_hit(output: dict, expected: dict) -> bool:
    retrieved = [c["metadata"].get("source") for c in output.get("chunks", [])]
    return any(src in retrieved for src in expected["expected_source"])


class JudgeVerdict(BaseModel):
    verdict: Literal["PASS", "FAIL"]
    reason: str = Field(description="Brief justification for the verdict")


JUDGE_TEMPLATE = """You are grading a RAG system's answer.

Question: {prompt}
Expected answer: {expected}
Generated answer: {response}

Decide whether the generated answer substantively addresses the question
AND aligns with the expected answer. Provide a brief reason."""


def answer_addresses_question(input: dict, output: dict, expected: dict) -> dict:
    judge_prompt = JUDGE_TEMPLATE.format(
        prompt=input["question"],
        expected=expected["expected_answer"],
        response=output["answer"][:2000],
    )
    result = _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        tools=[{
            "name": "record_verdict",
            "description": "Record the PASS/FAIL verdict on this answer.",
            "input_schema": JudgeVerdict.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "record_verdict"},
        messages=[{"role": "user", "content": judge_prompt}],
    )
    tool_block = next(b for b in result.content if b.type == "tool_use")
    verdict = JudgeVerdict(**tool_block.input)
    return {
        "score": 1 if verdict.verdict == "PASS" else 0,
        "label": verdict.verdict,
        "explanation": verdict.reason,
    }
