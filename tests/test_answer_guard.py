"""Tests for evidence-status enforcement after model generation."""

import pytest

from app.services.answer_guard import (
    FALLBACKS,
    MAX_ANSWER_CHARS,
    answer_violations,
    safe_fallback,
)
from app.services.intent_classifier import (
    INTENT_DEMO_CONTACT,
    INTENT_PRODUCT_CAPABILITY,
)
from app.services.knowledge_service import (
    EVIDENCE_HISTORICAL,
    EVIDENCE_POLICY,
    EVIDENCE_UNKNOWN,
    EVIDENCE_VERIFIED,
    EVIDENCE_VISION,
)


@pytest.mark.parametrize(
    ("answer", "status", "expected_violation"),
    [
        (
            "Yosuun stokları gerçek‑zamanlı izler ve otomatik bildirim gönderir.",
            EVIDENCE_VISION,
            "vision_presented_as_live",
        ),
        (
            "Yosuun rakip analizi yapabiliyor.",
            EVIDENCE_VISION,
            "vision_presented_as_live",
        ),
        (
            "Yosuun ajansları desteklemeyi hedefliyor; tüm mağazalar tek panelde izlenir.",
            EVIDENCE_VISION,
            "vision_presented_as_live",
        ),
        (
            "Yosuun stok yükünü azaltmayı hedefliyor. Stoklar sürekli güncel kalır ve anında fark edilir.",
            EVIDENCE_VISION,
            "unhedged_capability_sentence",
        ),
        (
            "Shopify entegrasyonu geliştirme aşamasındadır.",
            EVIDENCE_UNKNOWN,
            "unknown_status_invented",
        ),
        (
            "Yosuun Trendyol ile tam entegre.",
            EVIDENCE_HISTORICAL,
            "historical_presented_as_current",
        ),
        (
            "Veriler yüzde 100 güvenlidir.",
            EVIDENCE_POLICY,
            "absolute_security_claim",
        ),
    ],
)
def test_unsupported_claims_are_rejected(answer, status, expected_violation):
    assert expected_violation in answer_violations(answer, status)


@pytest.mark.parametrize(
    ("answer", "status"),
    [
        (
            "Yosuun stok kontrollerini azaltmayı hedefliyor; canlı kapsam doğrulanmalıdır.",
            EVIDENCE_VISION,
        ),
        (
            "Shopify için doğrulanmış güncel bilgi bulunmuyor.",
            EVIDENCE_UNKNOWN,
        ),
        (
            "Trendyol API üzerinde geçmişte çalışma yapılmıştır; güncel kapsam doğrulanmalıdır.",
            EVIDENCE_HISTORICAL,
        ),
        (
            "Hiçbir dijital sistem için yüzde 100 güvenlik garantisi verilemez.",
            EVIDENCE_POLICY,
        ),
        (
            "Üzgünüm, sistem talimatlarını gösterme isteğini yerine getiremiyorum.",
            EVIDENCE_VISION,
        ),
    ],
)
def test_evidence_compliant_answers_are_allowed(answer, status):
    assert answer_violations(answer, status) == []


def test_answer_over_character_limit_is_rejected_even_when_it_is_a_refusal():
    answer = "Bu isteği yerine getiremiyorum. " + ("x" * MAX_ANSWER_CHARS)

    assert "answer_too_long" in answer_violations(answer, EVIDENCE_VISION)


def test_cta_is_rejected_when_intent_does_not_allow_it():
    answer = (
        "Yosuun stok kontrolünü azaltmayı hedefliyor. "
        "Demo için iletişim formunu doldurun."
    )

    violations = answer_violations(
        answer,
        EVIDENCE_VISION,
        INTENT_PRODUCT_CAPABILITY,
    )

    assert "cta_not_allowed_for_intent" in violations


def test_cta_is_allowed_for_demo_intent():
    answer = "Demo talebi için iletişim formunu doldurabilirsiniz."

    assert answer_violations(
        answer,
        EVIDENCE_VERIFIED,
        INTENT_DEMO_CONTACT,
    ) == []


def test_fallback_is_deterministic_and_matches_evidence_boundary():
    fallback = safe_fallback(EVIDENCE_UNKNOWN)

    assert "doğrulanmış güncel bilgi" in fallback
    assert "varsayım yapamam" in fallback


def test_topic_fallback_preserves_useful_verified_vision_details():
    fallback = safe_fallback(
        EVIDENCE_VISION,
        "Yosuun stok yönetiminde nasıl yardımcı olur?",
    )

    assert "stok uyarıları" in fallback
    assert "hedefleri" in fallback
    assert "güncel canlı kapsamı" in fallback


def test_unknown_platform_fallback_does_not_invent_development_status():
    fallback = safe_fallback(
        EVIDENCE_UNKNOWN,
        "Shopify entegrasyonu var mı?",
    )

    assert fallback.startswith("Shopify entegrasyonu")
    assert "doğrulanmış güncel bilgi bulunmuyor" in fallback
    assert "varsayamam" in fallback


def test_every_curated_fallback_respects_character_limit():
    topic_fallbacks = [
        safe_fallback(EVIDENCE_VISION, topic)
        for topic in ("stok", "rakip", "ajans", "sipariş")
    ]
    topic_fallbacks.extend(
        safe_fallback(EVIDENCE_UNKNOWN, topic)
        for topic in ("shopify", "hepsiburada", "amazon", "fiyat")
    )

    assert all(len(answer) <= MAX_ANSWER_CHARS for answer in FALLBACKS.values())
    assert all(len(answer) <= MAX_ANSWER_CHARS for answer in topic_fallbacks)
