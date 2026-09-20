"""Deterministic 100-question routing evaluation for the Yosuun AI pipeline."""

from collections import Counter
import json
from pathlib import Path

from app.services.intent_classifier import IntentClassifier
from app.services.knowledge_service import KnowledgeService


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_PATH = ROOT / "tests" / "fixtures" / "ai_evaluation_cases.json"
KNOWLEDGE_PATH = ROOT / "knowledge" / "yosuun.md"


def _evaluation_cases():
    return json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))


def test_evaluation_dataset_has_100_balanced_unique_questions_without_answers():
    cases = _evaluation_cases()

    assert len(cases) == 100
    assert len({case["id"] for case in cases}) == 100
    assert len({case["question"] for case in cases}) == 100
    assert set(Counter(case["category"] for case in cases).values()) == {10}
    assert all("answer" not in case for case in cases)
    assert all(case["max_answer_chars"] == 250 for case in cases)


def test_all_evaluation_questions_match_intent_evidence_and_retrieval_contract():
    cases = _evaluation_cases()
    classifier = IntentClassifier()
    knowledge = KnowledgeService(KNOWLEDGE_PATH, classifier=classifier)

    failures = []
    for case in cases:
        intent = classifier.classify(case["question"])
        result = knowledge.retrieve_result(case["question"])

        if intent.name != case["expected_intent"]:
            failures.append(
                f"{case['id']} intent={intent.name}, "
                f"expected={case['expected_intent']}"
            )
        if intent.cta_allowed is not case["cta_allowed"]:
            failures.append(
                f"{case['id']} cta={intent.cta_allowed}, "
                f"expected={case['cta_allowed']}"
            )
        if result.evidence_status != case["expected_evidence"]:
            failures.append(
                f"{case['id']} evidence={result.evidence_status}, "
                f"expected={case['expected_evidence']}"
            )
        expected_heading = case["expected_heading"]
        if expected_heading and not any(
            expected_heading in title for title in result.section_titles
        ):
            failures.append(
                f"{case['id']} heading={expected_heading!r} missing from "
                f"{result.section_titles!r}"
            )
        if result.confidence not in {"low", "medium", "high"}:
            failures.append(
                f"{case['id']} invalid confidence={result.confidence!r}"
            )

    assert failures == [], "\n" + "\n".join(failures)
