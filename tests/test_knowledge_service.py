"""Tests for loading the complete simple-RAG knowledge document."""

import pytest

from app.services.knowledge_service import KnowledgeService, KnowledgeSourceError


def test_read_all_returns_the_complete_document_and_caches_it(tmp_path):
    source = tmp_path / "knowledge.md"
    source.write_text("# Birinci\nTam içerik\n\n# İkinci\nSon içerik", encoding="utf-8")
    service = KnowledgeService(source)

    first = service.read_all()
    source.write_text("değiştirildi", encoding="utf-8")
    second = service.read_all()

    assert first == "# Birinci\nTam içerik\n\n# İkinci\nSon içerik"
    assert second == first


def test_missing_document_raises_safe_error(tmp_path):
    service = KnowledgeService(tmp_path / "missing.md")

    with pytest.raises(KnowledgeSourceError, match="okunamadı"):
        service.read_all()


def test_empty_document_is_rejected(tmp_path):
    source = tmp_path / "empty.md"
    source.write_text("   \n", encoding="utf-8")

    with pytest.raises(KnowledgeSourceError, match="boş olamaz"):
        KnowledgeService(source).read_all()
