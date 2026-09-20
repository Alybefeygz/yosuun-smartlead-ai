"""Deterministic evidence-language checks for generated Yosuun answers."""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Sequence

from app.services.knowledge_service import (
    EVIDENCE_ATTRIBUTED,
    EVIDENCE_HISTORICAL,
    EVIDENCE_PILOT,
    EVIDENCE_POLICY,
    EVIDENCE_UNKNOWN,
    EVIDENCE_VERIFIED,
    EVIDENCE_VISION,
)


MAX_ANSWER_CHARS = 250


SAFE_REFUSALS = (
    "yerine getiremiyorum",
    "paylasamam",
    "gosteremem",
    "aciklayamam",
)

VISION_HEDGES = (
    "hedef",
    "amac",
    "vizyon",
    "kamuya acik urun anlatis",
    "gelistiriliyor",
)

VISION_OVERCLAIMS = (
    "gercek zaman",
    "anlik olarak",
    "yapabiliyor",
    "tek ekranda toplar",
    "verilerini takip eder",
    "verilerini izler",
    "degisiklikleri fark eder",
    "karar destegi sunar",
    "otomatiklestirir",
    "otomatiklestirerek",
    "otomatiklestirilir",
    "senkronizasyon saglar",
    "senkronizasyonu saglayarak",
    "otomatik olarak tespit edilir",
    "tespit edilir",
    "bildirim gonderilir",
    "yonetebilirsiniz",
    "panelde izlenir",
    "mumkun olur",
    "cozulur",
    "su anda guncelliyor",
    "tam entegre",
)

VISION_CAPABILITY_TERMS = (
    "stok",
    "rakip",
    "urun",
    "siparis",
    "kampanya",
    "operasyon",
    "entegrasyon",
    "otomatik",
    "uyari",
    "panel",
    "magaza",
    "veri",
    "performans",
)

VISION_BOUNDARIES = (*VISION_HEDGES, "dogrulan", "canli kapsam", "bilgi kaynag")

UNKNOWN_REQUIRED = (
    "dogrulanmis bilgi bulunmuyor",
    "dogrulanmis guncel bilgi",
    "bilgi kaynaginda yer almiyor",
    "bilgi su anda yok",
    "bilgi bulunmuyor",
    "dogrulanmamistir",
    "dogrulama gerekir",
    "net bilgi yok",
)

UNKNOWN_INVENTIONS = (
    "gelistirme asamasinda",
    "pilot asamasinda",
    "test asamasinda",
    "test surecinde",
    "henuz yayina alinmamis",
    "entegrasyonu mevcuttur",
    "tam entegre",
)

HISTORICAL_REQUIRED = (
    "gecmis",
    "uzerinde calisil",
    "calisma yapil",
    "tarihsel",
)

ATTRIBUTION_REQUIRED = (
    "kamuya acik",
    "urun iletisim",
    "web sites",
    "linkedin",
    "paylasilmis",
)

ABSOLUTE_SECURITY_CLAIMS = (
    "yuzde 100 guvenli",
    "100 guvenli",
    "tamamen guvenli",
    "mutlak guvenli",
    "guvenli bir sekilde saklanir",
    "guvenli sekilde saklanir",
)

FALLBACKS: Dict[str, str] = {
    EVIDENCE_UNKNOWN: (
        "Bu konuda doğrulanmış güncel bilgi kaynağımda bulunmuyor. Geliştirme, "
        "pilot veya canlı kullanım durumu hakkında varsayım yapamam. En güncel "
        "bilgi için Yosuun ekibinden doğrulama alınması gerekir."
    ),
    EVIDENCE_HISTORICAL: (
        "Bu konuda geçmişte çalışma yapıldığı belirtiliyor; ancak güncel canlı "
        "kapsam ve desteklenen işlemler doğrulanmamıştır."
    ),
    EVIDENCE_VISION: (
        "Bu konu Yosuun'un ürün vizyonunda yer alıyor ve operasyon yükünü "
        "azaltmayı hedefliyor. Güncel canlı özellik kapsamı bilgi kaynağında "
        "doğrulanmadığı için mevcut bir yetenek gibi sunamam."
    ),
    EVIDENCE_ATTRIBUTED: (
        "Bu bilgi Yosuun'un kamuya açık ürün iletişiminde paylaşılmış bir iddiadır; "
        "bağımsız doğrulanmış sonuç veya garanti olarak sunulamaz."
    ),
    EVIDENCE_POLICY: (
        "Bu konuda mutlak bir garanti verilemez. Yalnızca güncel kurumsal politika "
        "ve doğrulanmış kapsam dikkate alınmalıdır."
    ),
    EVIDENCE_PILOT: (
        "Yosuun genel olarak geliştirme/demo/pilot aşamasındadır. Bu genel durum, "
        "belirli bir özelliğin veya entegrasyonun pilotta olduğunu kanıtlamaz."
    ),
    EVIDENCE_VERIFIED: (
        "Bu soruya doğrulanmış bilgi sınırları içinde güvenli bir cevap üretilemedi."
    ),
}


def _normalize(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold().replace("ı", "i"))
    without_marks = "".join(
        character
        for character in folded
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def answer_violations(answer: str, evidence_status: str) -> List[str]:
    """Return machine-readable reasons an answer exceeds its evidence status."""

    normalized = _normalize(answer)
    violations: List[str] = []
    if len(answer) > MAX_ANSWER_CHARS:
        violations.append("answer_too_long")
    if any(phrase in normalized for phrase in SAFE_REFUSALS):
        return violations

    if evidence_status == EVIDENCE_VISION:
        if not any(phrase in normalized for phrase in VISION_HEDGES):
            violations.append("vision_language_missing")
        if any(phrase in normalized for phrase in VISION_OVERCLAIMS):
            violations.append("vision_presented_as_live")
        sentences = [
            _normalize(sentence)
            for sentence in re.split(r"[.!?\n]+", answer)
            if sentence.strip()
        ]
        if any(
            any(term in sentence for term in VISION_CAPABILITY_TERMS)
            and not any(boundary in sentence for boundary in VISION_BOUNDARIES)
            for sentence in sentences
        ):
            violations.append("unhedged_capability_sentence")
    elif evidence_status == EVIDENCE_UNKNOWN:
        has_unknown_boundary = any(
            phrase in normalized for phrase in UNKNOWN_REQUIRED
        ) or (
            "bilgi" in normalized
            and any(
                phrase in normalized
                for phrase in ("yok", "bulunmuyor", "yer almiyor", "dogrulanma")
            )
        )
        if not has_unknown_boundary:
            violations.append("unknown_boundary_missing")
        if any(phrase in normalized for phrase in UNKNOWN_INVENTIONS):
            violations.append("unknown_status_invented")
    elif evidence_status == EVIDENCE_HISTORICAL:
        if not any(phrase in normalized for phrase in HISTORICAL_REQUIRED):
            violations.append("historical_attribution_missing")
        if "tam entegre" in normalized or "su anda aktif" in normalized:
            violations.append("historical_presented_as_current")
    elif evidence_status == EVIDENCE_ATTRIBUTED:
        if not any(phrase in normalized for phrase in ATTRIBUTION_REQUIRED):
            violations.append("public_attribution_missing")
    elif evidence_status == EVIDENCE_POLICY:
        explicit_caveat = any(
            phrase in normalized
            for phrase in ("garantisi verilemez", "garanti verilemez", "garanti edilemez")
        )
        if (
            any(phrase in normalized for phrase in ABSOLUTE_SECURITY_CLAIMS)
            and not explicit_caveat
        ):
            violations.append("absolute_security_claim")
    elif evidence_status == EVIDENCE_PILOT:
        if "pilot" not in normalized and "gelistirme" not in normalized:
            violations.append("pilot_boundary_missing")
    return violations


def build_repair_instruction(violations: Sequence[str], evidence_status: str) -> str:
    """Build a concise correction request while keeping evidence rules authoritative."""

    joined = ", ".join(violations)
    return (
        "Önceki taslak kanıt statüsü kurallarını ihlal etti. "
        f"Kanıt statüsü: {evidence_status}. İhlaller: {joined}. "
        "Cevabı yalnız sağlanan bilgi bağlamına dayanarak yeniden yaz. "
        "Yeni özellik veya durum uydurma; doğrudan soruyu cevapla ve gereksiz "
        "demo/iletişim çağrısı ekleme. Boşluklar ve noktalama işaretleri "
        f"dâhil en fazla {MAX_ANSWER_CHARS} karakter kullan. Yalnız düzeltilmiş "
        "nihai cevabı ver."
    )


def safe_fallback(evidence_status: str, query: str = "") -> str:
    """Return a deterministic, topic-aware answer when correction remains unsafe."""

    normalized_query = _normalize(query)
    if evidence_status == EVIDENCE_VISION:
        if "stok" in normalized_query:
            return (
                "Yosuun'un ürün vizyonunda stok verilerini izleme, kritik durumları "
                "fark etme, stok uyarıları üretme ve manuel stok kontrolünü azaltma "
                "hedefleri yer alır. Bunların güncel canlı kapsamı ve desteklenen "
                "entegrasyonları ayrıca doğrulanmalıdır."
            )
        if "rakip" in normalized_query:
            return (
                "Yosuun'un ürün vizyonunda rakip verilerini takip etme, karşılaştırma "
                "ve karar desteğine dönüştürme hedefi yer alır. Güncel canlı özellik "
                "kapsamı bilgi kaynağında doğrulanmamıştır."
            )
        if "ajans" in normalized_query:
            return (
                "Yosuun, ajansların birden fazla marka operasyonunu merkezi yönetmesini, "
                "manuel kontrolleri azaltmasını ve ekip kapasitesini verimli kullanmasını "
                "hedefler. Bu bir ürün vizyonudur; güncel canlı kapsam ayrıca doğrulanmalıdır."
            )
        if "siparis" in normalized_query:
            return (
                "Sipariş akışı Yosuun'un çözmeyi hedeflediği operasyon alanlarından "
                "biridir. Otomatik onay, iptal veya kargolama gibi belirli işlemlerin "
                "güncel canlı kapsamı doğrulanmamıştır."
            )
    if evidence_status == EVIDENCE_UNKNOWN:
        platforms = {
            "shopify": "Shopify",
            "hepsiburada": "Hepsiburada",
            "amazon": "Amazon",
            "n11": "N11",
            "woocommerce": "WooCommerce",
            "ciceksepeti": "ÇiçekSepeti",
            "ikas": "ikas",
        }
        for token, display_name in platforms.items():
            if token in normalized_query:
                return (
                    f"{display_name} entegrasyonu ve bu platformda desteklenen otomatik "
                    "işlemler hakkında doğrulanmış güncel bilgi bulunmuyor. Bunun "
                    "geliştirme, pilot, test veya canlı aşamada olduğunu varsayamam."
                )
        if any(token in normalized_query for token in ("fiyat", "paket", "ucret")):
            return (
                "Yosuun'un güncel doğrulanmış fiyat veya paket bilgisi bilgi kaynağında "
                "bulunmuyor. Herhangi bir ücret, paket adı veya indirim uyduramam."
            )
    return FALLBACKS.get(evidence_status, FALLBACKS[EVIDENCE_UNKNOWN])
