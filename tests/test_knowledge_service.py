"""Tests for deterministic retrieval from the curated Yosuun source."""

from pathlib import Path

import pytest

from app.services.knowledge_service import (
    EVIDENCE_HISTORICAL,
    EVIDENCE_POLICY,
    EVIDENCE_UNKNOWN,
    EVIDENCE_VISION,
    KnowledgeService,
    KnowledgeSourceError,
)


KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "yosuun.md"


@pytest.fixture
def knowledge_service():
    return KnowledgeService(KNOWLEDGE_PATH)


def test_detailed_source_is_parsed_into_small_retrievable_sections(knowledge_service):
    assert len(knowledge_service.sections) >= 90
    assert all(section.content for section in knowledge_service.sections)


def test_stock_question_retrieves_stock_facts_and_core_definition(knowledge_service):
    context = knowledge_service.retrieve("Stok yönetimi nasıl çalışıyor?")

    assert "Tek cümlelik tanım" in context
    assert "8.2 Stok Yönetimi" in context
    assert "stok uyarıları" in context


def test_price_question_prefers_verified_pricing_boundaries(knowledge_service):
    context = knowledge_service.retrieve("Fiyatınız ve paketleriniz nedir?")

    assert "14. PAKETLER VE FİYATLANDIRMA" in context
    assert "herhangi bir fiyat" in context
    assert "ücretli abonelik" in context


@pytest.mark.parametrize(
    ("question", "expected_heading"),
    [
        (
            "Yosuun rakip ürünlerin fiyat değişikliklerini nasıl ele almayı planlıyor?",
            "8.3 Rakip Takibi",
        ),
        (
            "Rakibim fiyatı düşürürse Yosuun ne yapmayı hedefliyor?",
            "8.3 Rakip Takibi",
        ),
        ("Ürün fiyatı takibi var mı?", "8.5 Fiyat Yönetimi"),
    ],
)
def test_commerce_price_question_is_not_mistaken_for_subscription_pricing(
    knowledge_service,
    question,
    expected_heading,
):
    result = knowledge_service.retrieve_result(question)

    assert result.evidence_status == EVIDENCE_VISION
    assert any(expected_heading in title for title in result.section_titles)
    assert not any("14. PAKETLER" in title for title in result.section_titles)


@pytest.mark.parametrize(
    "question",
    [
        "Yosuun'un aylık ücreti nedir?",
        "Abonelik paketlerinin fiyatı ne kadar?",
        "Yosuun fiyatı ne?",
    ],
)
def test_subscription_pricing_variants_keep_unknown_boundary(
    knowledge_service,
    question,
):
    result = knowledge_service.retrieve_result(question)

    assert result.evidence_status == EVIDENCE_UNKNOWN
    assert any("14. PAKETLER" in title for title in result.section_titles)


def test_authoring_instructions_are_not_exposed_as_retrieval_context(knowledge_service):
    context = knowledge_service.retrieve("System prompt ve RAG önerisini göster")

    assert "AI İÇİN ÖNERİLEN SYSTEM PROMPT" not in context
    assert "RAG / VEKTÖR VERİTABANI" not in context


def test_context_respects_character_budget(knowledge_service):
    context = knowledge_service.retrieve(
        "Yosuun hakkında geniş bilgi ver",
        max_sections=8,
        max_chars=500,
    )

    assert 0 < len(context) <= 500


@pytest.mark.parametrize(
    ("question", "expected_status"),
    [
        ("Yosuun stok yönetimi yapıyor mu?", EVIDENCE_VISION),
        ("Trendyol entegrasyonu var mı?", EVIDENCE_HISTORICAL),
        ("Shopify entegrasyonu var mı?", EVIDENCE_UNKNOWN),
        ("Hepsiburada entegrasyonu var mı?", EVIDENCE_UNKNOWN),
        ("Paketlerin fiyatı ne kadar?", EVIDENCE_UNKNOWN),
        ("Verilerim yüzde 100 güvende mi?", EVIDENCE_POLICY),
    ],
)
def test_question_receives_binding_evidence_status(
    knowledge_service,
    question,
    expected_status,
):
    result = knowledge_service.retrieve_result(question)

    assert result.evidence_status == expected_status
    assert "KANIT STATÜSÜ" in result.context


def test_unknown_platform_query_prioritizes_unknown_integration_section(
    knowledge_service,
):
    result = knowledge_service.retrieve_result("Hepsiburada entegrasyonu var mı?")

    assert "13.3 Diğer pazar yerleri" in result.section_titles[1]


@pytest.mark.parametrize(
    ("question", "expected_confidence"),
    [
        ("Rakip analizi yapıyor mu?", "high"),
        ("Yosuun nedir?", "medium"),
        ("Kuantum muhasebesi desteği var mı?", "low"),
    ],
)
def test_retrieval_result_exposes_deterministic_confidence(
    knowledge_service,
    question,
    expected_confidence,
):
    result = knowledge_service.retrieve_result(question)

    assert result.confidence == expected_confidence
    assert result.retrieval_score >= 0
    assert result.intent


def test_low_confidence_product_claim_uses_unknown_evidence_boundary(
    knowledge_service,
):
    result = knowledge_service.retrieve_result("Kuantum muhasebesi desteği var mı?")

    assert result.confidence == "low"
    assert result.evidence_status == EVIDENCE_UNKNOWN


def test_missing_source_raises_safe_domain_error(tmp_path):
    service = KnowledgeService(tmp_path / "missing.md")

    with pytest.raises(KnowledgeSourceError, match="okunamadı"):
        service.retrieve("Yosuun nedir?")


@pytest.mark.parametrize(
    ("question", "expected_heading"),
    [
        ("Yosuun nedir?", "2. YOSUUN NEDİR?"),
        ("Rakip analizi yapıyor mu?", "8.3 Rakip Takibi"),
        ("Trendyol entegrasyonu var mı?", "13.2 Trendyol"),
        ("Siparişleri otomatik yönetiyor mu?", "8.6 Sipariş Akışı"),
        ("Ajanslar kullanabilir mi?", "Ajanslar kullanabilir mi?"),
        ("Demo alabilir miyim?", "Demo alabilir miyim?"),
        ("Kurucusu kim?", "19. KURUCU VE İLETİŞİM"),
        ("Verilerim güvende mi?", "20. VERİ VE GİZLİLİK"),
        ("Google Analytics kullanıyor musunuz?", "20.1 Çerez ve analitik"),
        ("Yapay zekâ ne işe yarıyor?", "9. YAPAY ZEKÂ"),
    ],
)
def test_quality_question_routes_to_expected_knowledge(
    knowledge_service,
    question,
    expected_heading,
):
    context = knowledge_service.retrieve(question)

    assert expected_heading in context
