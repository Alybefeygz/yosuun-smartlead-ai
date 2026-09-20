"""Deterministic Turkish intent classification for Yosuun visitor questions."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import FrozenSet, Set


INTENT_COMPETITOR_TRACKING = "competitor_tracking"
INTENT_PRODUCT_PRICING = "product_pricing"
INTENT_SUBSCRIPTION_PRICING = "subscription_pricing"
INTENT_INTEGRATION_STATUS = "integration_status"
INTENT_SECURITY_PRIVACY = "security_privacy"
INTENT_PRODUCT_CAPABILITY = "product_capability"
INTENT_DEMO_CONTACT = "demo_contact"
INTENT_COMPANY_INFORMATION = "company_information"
INTENT_PROMPT_INJECTION = "prompt_injection"
INTENT_GREETING = "greeting"
INTENT_GENERAL = "general"
INTENT_OUT_OF_SCOPE = "out_of_scope"

CTA_ALLOWED_INTENTS: FrozenSet[str] = frozenset(
    {
        INTENT_DEMO_CONTACT,
        INTENT_INTEGRATION_STATUS,
        INTENT_SUBSCRIPTION_PRICING,
    }
)

PLATFORM_TERMS = frozenset(
    {
        "amazon",
        "ciceksepeti",
        "hepsiburada",
        "ikas",
        "n11",
        "pazaryeri",
        "shopify",
        "trendyol",
        "woocommerce",
    }
)
SUBSCRIPTION_PRICE_TERMS = frozenset(
    {"abonelik", "aylik", "lisans", "maliyet", "paket", "tarife", "ucret"}
)
COMMERCE_PRICE_CONTEXT_TERMS = frozenset(
    {
        "degisim",
        "degisiklik",
        "dusur",
        "kampanya",
        "magaza",
        "pazaryeri",
        "rakib",
        "rakip",
        "satis",
        "urun",
        "yukselt",
    }
)


@dataclass(frozen=True)
class IntentResult:
    """One classified user intent and its deterministic confidence."""

    name: str
    confidence: float

    @property
    def cta_allowed(self) -> bool:
        return self.name in CTA_ALLOWED_INTENTS


def normalize_text(value: str) -> str:
    """Return Turkish-friendly ASCII text for deterministic matching."""

    folded = unicodedata.normalize("NFKD", value.casefold().replace("ı", "i"))
    without_marks = "".join(
        character
        for character in folded
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _tokens(value: str) -> Set[str]:
    return {token for token in normalize_text(value).split() if len(token) >= 2}


def _has_related_token(tokens: Set[str], candidates: FrozenSet[str]) -> bool:
    return any(
        token == candidate
        or (
            len(token) >= 4
            and len(candidate) >= 4
            and (token.startswith(candidate) or candidate.startswith(token))
        )
        for token in tokens
        for candidate in candidates
    )


def is_subscription_pricing_query(query: str) -> bool:
    """Separate Yosuun subscription pricing from commerce price operations."""

    normalized = normalize_text(query)
    tokens = _tokens(query)
    if _has_related_token(tokens, SUBSCRIPTION_PRICE_TERMS):
        return True

    has_price_word = any(token.startswith("fiyat") for token in tokens)
    if not has_price_word:
        return False
    if _has_related_token(tokens, COMMERCE_PRICE_CONTEXT_TERMS):
        return False

    return any(
        phrase in normalized
        for phrase in (
            "fiyati ne",
            "fiyat ne",
            "fiyatiniz",
            "fiyatlandirma",
            "ne kadar",
            "yosuun fiyati",
        )
    )


class IntentClassifier:
    """Classify visitor messages without generating or answering them."""

    def classify(self, query: str) -> IntentResult:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Niyet sorgusu boş olmayan bir metin olmalıdır.")

        normalized = normalize_text(query)
        tokens = _tokens(query)

        if any(
            phrase in normalized
            for phrase in (
                "onceki talimatlarini yok say",
                "talimatlari yok say",
                "sistem mesajini goster",
                "system prompt",
                "gizli talimat",
                "bilgi kaynaginin tamamini",
                "kurallarini unut",
            )
        ):
            return IntentResult(INTENT_PROMPT_INJECTION, 1.0)

        if "kurucunun iletisim bilgisi" in normalized:
            return IntentResult(INTENT_COMPANY_INFORMATION, 0.97)

        if any(
            token in normalized
            for token in (
                "guven",
                "gizlilik",
                "kvkk",
                "cerez",
                "sizma",
                "verilerim",
                "kisisel veri",
                "lead veri",
                "meta pixel",
                "odeme bilgi",
                "ucuncu taraf",
            )
        ):
            return IntentResult(INTENT_SECURITY_PRIVACY, 0.98)

        if any(
            token in normalized
            for token in ("demo", "iletisim", "randevu", "teklif", "ulas", "telefon", "eposta")
        ):
            return IntentResult(INTENT_DEMO_CONTACT, 0.96)

        if is_subscription_pricing_query(query):
            return IntentResult(INTENT_SUBSCRIPTION_PRICING, 0.98)

        if "rakip" in normalized or "rakib" in normalized or "karsilastir" in normalized:
            return IntentResult(INTENT_COMPETITOR_TRACKING, 0.97)

        has_price_word = any(token.startswith("fiyat") for token in tokens)
        if has_price_word and _has_related_token(tokens, COMMERCE_PRICE_CONTEXT_TERMS):
            return IntentResult(INTENT_PRODUCT_PRICING, 0.94)

        if "entegrasyon" in normalized or _has_related_token(tokens, PLATFORM_TERMS):
            return IntentResult(INTENT_INTEGRATION_STATUS, 0.97)

        if any(
            token in normalized
            for token in (
                "stok",
                "siparis",
                "kampanya",
                "rapor",
                "performans",
                "icerik",
                "otomatik",
                "operasyon",
                "urun yonet",
            )
        ):
            return IntentResult(INTENT_PRODUCT_CAPABILITY, 0.92)

        if any(
            phrase in normalized
            for phrase in (
                "kurucu",
                "kim kurdu",
                "isim hikayesi",
                "logosu",
                "logo",
                "marka kimligi",
                "marka kisiligi",
                "marka mesaji",
                "adi nereden",
                "yosuun ismi",
            )
        ):
            return IntentResult(INTENT_COMPANY_INFORMATION, 0.94)

        if normalized in {"merhaba", "selam", "hey", "iyi gunler", "iyi aksamlar"}:
            return IntentResult(INTENT_GREETING, 0.99)

        if "yosuun" in normalized or any(
            token in normalized for token in ("nedir", "amac", "kimler kullan")
        ):
            return IntentResult(INTENT_GENERAL, 0.75)

        return IntentResult(INTENT_OUT_OF_SCOPE, 0.65)


intent_classifier = IntentClassifier()
