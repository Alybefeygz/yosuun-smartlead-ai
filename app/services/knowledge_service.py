"""Local retrieval for the curated Yosuun Markdown knowledge base."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.services.intent_classifier import (
    INTENT_COMPANY_INFORMATION,
    INTENT_COMPETITOR_TRACKING,
    INTENT_DEMO_CONTACT,
    INTENT_GREETING,
    INTENT_OUT_OF_SCOPE,
    INTENT_PROMPT_INJECTION,
    INTENT_PRODUCT_CAPABILITY,
    INTENT_SECURITY_PRIVACY,
    INTENT_SUBSCRIPTION_PRICING,
    IntentClassifier,
    intent_classifier,
)


HEADING_PATTERN = re.compile(r"^(#{1,2})\s+(.+?)\s*$")
TOP_LEVEL_NUMBER_PATTERN = re.compile(r"^(\d+)\.")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# These chapters contain authoring instructions rather than visitor-facing facts.
RETRIEVAL_EXCLUDED_CHAPTERS = frozenset({"1", "34", "35", "36", "37", "38"})

EVIDENCE_VERIFIED = "verified_fact"
EVIDENCE_VISION = "product_vision"
EVIDENCE_HISTORICAL = "historical"
EVIDENCE_UNKNOWN = "unknown"
EVIDENCE_ATTRIBUTED = "attributed_claim"
EVIDENCE_POLICY = "policy"
EVIDENCE_PILOT = "pilot"

EVIDENCE_GUIDANCE = {
    EVIDENCE_VERIFIED: (
        "DOĞRULANMIŞ OLGU",
        "Yalnız bölümde açıkça yazan olguyu söyle; kapsamını genişletme.",
    ),
    EVIDENCE_VISION: (
        "ÜRÜN VİZYONU",
        "Yalnız 'hedefliyor', 'amaçlıyor' veya 'ürün vizyonunda' dili kullan; "
        "özelliği şu anda çalışan yetenek gibi sunma.",
    ),
    EVIDENCE_HISTORICAL: (
        "TARİHSEL ÇALIŞMA",
        "Yalnız geçmişte çalışma yapıldığını söyle; güncel canlı entegrasyon veya "
        "özellik sonucunu çıkarma.",
    ),
    EVIDENCE_UNKNOWN: (
        "BİLİNMİYOR / DOĞRULANMADI",
        "Doğrulanmış güncel bilgi olmadığını söyle; geliştirme, pilot, test veya "
        "canlı durum hakkında varsayım yapma.",
    ),
    EVIDENCE_ATTRIBUTED: (
        "ATFEDİLMİŞ KAMUYA AÇIK İDDİA",
        "Bilgiyi kamuya açık ürün iletişimine atfet; bağımsız doğrulanmış sonuç veya "
        "garanti gibi sunma.",
    ),
    EVIDENCE_POLICY: (
        "POLİTİKA / GÜVENLİK SINIRI",
        "Politikayı tam sınırlarıyla aktar; mutlak güvenlik veya değişmezlik garantisi verme.",
    ),
    EVIDENCE_PILOT: (
        "GENEL ÜRÜN PİLOT DURUMU",
        "Yalnız ürünün genel pilot durumunu söyle; bu statüyü tek bir entegrasyonun "
        "veya özelliğin pilotta olduğu sonucuna dönüştürme.",
    ),
}

STOP_WORDS = frozenset(
    {
        "acaba",
        "ama",
        "bana",
        "ben",
        "bir",
        "bu",
        "da",
        "de",
        "icin",
        "ile",
        "mi",
        "midir",
        "mu",
        "mudur",
        "nasil",
        "ne",
        "ve",
        "veya",
        "var",
        "yosuun",
    }
)

TOPIC_ALIASES: Dict[str, Set[str]] = {
    "genel": {"amac", "hakkinda", "nedir", "platform", "tanim"},
    "entegrasyon": {
        "amazon",
        "ciceksepeti",
        "entegrasyon",
        "hepsiburada",
        "ikas",
        "n11",
        "pazaryeri",
        "shopify",
        "trendyol",
        "woocommerce",
    },
    "fiyat": {"abonelik", "fiyat", "indirim", "paket", "ucret"},
    "iletisim": {"adres", "demo", "eposta", "iletisim", "mail", "telefon"},
    "guvenlik": {"cerez", "guvenli", "guvenlik", "gizlilik", "kvkk", "veri"},
    "hedef": {"ajans", "hedef", "kimler", "kobi", "kullanici", "marka", "satici"},
    "rakip": {"analiz", "karsilastirma", "rakib", "rakip", "takip"},
    "stok": {"envanter", "senkronizasyon", "stok", "uyari"},
    "teknoloji": {"altyapi", "backend", "flask", "groq", "mimari", "model", "teknoloji"},
}

class KnowledgeSourceError(RuntimeError):
    """Raised when the curated knowledge source cannot be loaded safely."""


@dataclass(frozen=True)
class KnowledgeSection:
    """One independently retrievable Markdown section."""

    chapter: str
    title: str
    content: str
    order: int
    evidence_status: str
    normalized_title: str
    normalized_content: str


@dataclass(frozen=True)
class RetrievalResult:
    """Formatted context plus the strictest answer mode for the current query."""

    context: str
    evidence_status: str
    section_titles: Tuple[str, ...]
    intent: str = "general"
    retrieval_score: int = 0
    confidence: str = "low"


def _normalize(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold().replace("ı", "i"))
    without_marks = "".join(
        character
        for character in folded
        if unicodedata.category(character) != "Mn"
    )
    return " ".join(TOKEN_PATTERN.findall(without_marks))


def _tokens(value: str) -> Set[str]:
    return {
        token
        for token in _normalize(value).split()
        if len(token) >= 3 and token not in STOP_WORDS
    }


def _token_sets_overlap(left: Set[str], right: Set[str]) -> bool:
    return any(
        left_token == right_token
        or (
            len(left_token) >= 4
            and len(right_token) >= 4
            and (
                left_token.startswith(right_token)
                or right_token.startswith(left_token)
            )
        )
        for left_token in left
        for right_token in right
    )


def _expanded_query_tokens(query: str) -> Set[str]:
    tokens = _tokens(query)
    expanded = set(tokens)
    matched_topics = [
        (topic, aliases)
        for topic, aliases in TOPIC_ALIASES.items()
        if _token_sets_overlap(tokens, aliases)
    ]
    has_specific_topic = any(topic != "genel" for topic, _aliases in matched_topics)
    for topic, aliases in matched_topics:
        if topic == "genel" and has_specific_topic:
            continue
        expanded.add(topic)
    return expanded


class KnowledgeService:
    """Parse, rank and format relevant parts of the Yosuun knowledge source."""

    def __init__(
        self,
        source_path: Path,
        classifier: Optional[IntentClassifier] = None,
    ) -> None:
        self.source_path = Path(source_path)
        self.intent_classifier = classifier or intent_classifier
        self._sections: Optional[List[KnowledgeSection]] = None

    @property
    def sections(self) -> Sequence[KnowledgeSection]:
        """Load once per process and expose an immutable view of parsed sections."""

        if self._sections is None:
            self._sections = self._load_sections()
        return tuple(self._sections)

    def retrieve(
        self,
        query: str,
        *,
        max_sections: int = 4,
        max_chars: int = 7000,
    ) -> str:
        """Return compact, relevant and ordered context for one visitor question."""

        return self.retrieve_result(
            query,
            max_sections=max_sections,
            max_chars=max_chars,
        ).context

    def retrieve_result(
        self,
        query: str,
        *,
        max_sections: int = 4,
        max_chars: int = 7000,
    ) -> RetrievalResult:
        """Return context and a machine-readable evidence contract."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Bilgi arama sorgusu boş olmayan bir metin olmalıdır.")
        if max_sections <= 0 or max_chars <= 0:
            raise ValueError("Bilgi arama limitleri pozitif olmalıdır.")

        query_tokens = _expanded_query_tokens(query)
        normalized_query = _normalize(query)
        intent_result = self.intent_classifier.classify(query)
        ranked = sorted(
            (
                (
                    self._score(
                        section,
                        query_tokens,
                        normalized_query,
                        intent_result.name,
                    ),
                    section,
                )
                for section in self.sections
            ),
            key=lambda item: (-item[0], item[1].order),
        )

        selected: List[KnowledgeSection] = []
        relevant: List[KnowledgeSection] = []
        relevant_scores: List[int] = []
        core = self._core_section()
        if core is not None:
            selected.append(core)

        for score, section in ranked:
            if score <= 0 or section in selected:
                continue
            selected.append(section)
            relevant.append(section)
            relevant_scores.append(score)
            if len(selected) >= max_sections:
                break

        retrieval_score = relevant_scores[0] if relevant_scores else 0
        confidence = self._retrieval_confidence(
            intent_result.name,
            retrieval_score,
        )
        evidence_status = self._answer_status(
            query,
            relevant,
            core,
            intent_result.name,
            confidence,
        )
        return RetrievalResult(
            context=self._format_with_budget(selected, max_chars),
            evidence_status=evidence_status,
            section_titles=tuple(section.title for section in selected),
            intent=intent_result.name,
            retrieval_score=retrieval_score,
            confidence=confidence,
        )

    def _load_sections(self) -> List[KnowledgeSection]:
        try:
            markdown = self.source_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise KnowledgeSourceError(
                f"Yosuun bilgi kaynağı okunamadı: {self.source_path}"
            ) from exc

        sections: List[KnowledgeSection] = []
        current_chapter = ""
        current_title = ""
        current_lines: List[str] = []
        current_excluded = False

        def flush() -> None:
            content = "\n".join(current_lines).strip()
            if not current_title or not content or current_excluded:
                return
            sections.append(
                KnowledgeSection(
                    chapter=current_chapter,
                    title=current_title,
                    content=content,
                    order=len(sections),
                    evidence_status=self._classify_section(
                        current_chapter,
                        current_title,
                    ),
                    normalized_title=_normalize(current_title),
                    normalized_content=_normalize(content),
                )
            )

        for line in markdown.splitlines():
            match = HEADING_PATTERN.match(line)
            if not match:
                if current_title:
                    current_lines.append(line)
                continue

            flush()
            current_lines = []
            level, title = match.groups()
            if level == "#":
                current_chapter = title
                number_match = TOP_LEVEL_NUMBER_PATTERN.match(title)
                chapter_number = number_match.group(1) if number_match else ""
                current_excluded = chapter_number in RETRIEVAL_EXCLUDED_CHAPTERS
                current_title = title
            else:
                current_title = f"{current_chapter} / {title}"

        flush()
        if not sections:
            raise KnowledgeSourceError("Yosuun bilgi kaynağında kullanılabilir bölüm yok.")
        return sections

    @staticmethod
    def _score(
        section: KnowledgeSection,
        query_tokens: Iterable[str],
        normalized_query: str,
        intent: str,
    ) -> int:
        title_tokens = set(section.normalized_title.split())
        content_tokens = set(section.normalized_content.split())
        score = 0
        for token in query_tokens:
            if KnowledgeService._has_related_token(token, title_tokens):
                score += 8
            elif KnowledgeService._has_related_token(token, content_tokens):
                score += 2
            if (
                token in TOPIC_ALIASES["entegrasyon"]
                and token not in {"entegrasyon", "pazaryeri"}
                and token in content_tokens
            ):
                score += 30
        if (
            intent == INTENT_COMPETITOR_TRACKING
            and "8 3 rakip takibi" in section.normalized_title
        ):
            score += 24
        if intent == INTENT_PRODUCT_CAPABILITY:
            capability_headings = {
                "stok": "8 2 stok yonetimi",
                "siparis": "8 6 siparis akisi",
                "kampanya": "8 7 kampanya yonetimi",
                "performans": "8 8 performans takibi",
                "planlama": "8 9 planlama",
                "icerik": "8 10 icerik surecleri",
                "rapor": "8 11 raporlama",
                "merkezi": "8 1 merkezi e ticaret yonetimi",
                "urun yonet": "8 4 urun yonetimi",
            }
            for query_term, heading in capability_headings.items():
                if query_term in normalized_query and heading in section.normalized_title:
                    score += 24
        if intent == INTENT_DEMO_CONTACT:
            if "demo" in normalized_query and (
                "demo alabilir" in section.normalized_title
                or section.chapter.startswith("15.")
            ):
                score += 30
            elif "demo" not in normalized_query and section.chapter.startswith("19."):
                score += 30
        if intent == INTENT_COMPANY_INFORMATION:
            company_targets = {
                "kurucu": "19.",
                "kim kurdu": "19.",
                "isim": "4.",
                "adi nereden": "4.",
                "logo": "24.",
                "sembol": "24.",
                "marka kimligi": "23.",
                "marka kisiligi": "23.",
                "marka mesaji": "5.",
            }
            for query_term, chapter_prefix in company_targets.items():
                if query_term in normalized_query and section.chapter.startswith(chapter_prefix):
                    score += 30
        if len(normalized_query) >= 5 and normalized_query in section.normalized_content:
            score += 12
        price_intent = intent == INTENT_SUBSCRIPTION_PRICING
        if price_intent and section.chapter.startswith("14."):
            score += 30
        elif not price_intent and section.chapter.startswith("14."):
            score -= 30
        security_intent = intent == INTENT_SECURITY_PRIVACY
        if security_intent and section.chapter.startswith("20."):
            score += 24
        return score

    @staticmethod
    def _retrieval_confidence(intent: str, top_score: int) -> str:
        """Convert deterministic ranking strength into a prompt contract."""

        if intent in {INTENT_OUT_OF_SCOPE, INTENT_PROMPT_INJECTION}:
            return "low"
        if top_score >= 24:
            return "high"
        if top_score >= 8:
            return "medium"
        return "low"

    @staticmethod
    def _has_related_token(token: str, candidates: Set[str]) -> bool:
        """Match common Turkish suffix variants without a heavyweight stemmer."""

        if token in candidates:
            return True
        if len(token) < 4:
            return False
        return any(
            len(candidate) >= 4
            and (candidate.startswith(token) or token.startswith(candidate))
            for candidate in candidates
        )

    def _core_section(self) -> Optional[KnowledgeSection]:
        for section in self.sections:
            if "tek cumlelik tanim" in section.normalized_title:
                return section
        return None

    @staticmethod
    def _classify_section(chapter: str, title: str) -> str:
        number_match = TOP_LEVEL_NUMBER_PATTERN.match(chapter)
        chapter_number = number_match.group(1) if number_match else ""
        normalized_title = _normalize(title)

        if chapter_number == "13":
            if "13 2 trendyol" in normalized_title:
                return EVIDENCE_HISTORICAL
            if "13 3 diger pazar yerleri" in normalized_title:
                return EVIDENCE_UNKNOWN
            return EVIDENCE_VISION
        if chapter_number == "14":
            return EVIDENCE_UNKNOWN
        if chapter_number == "15":
            return EVIDENCE_PILOT
        if chapter_number in {"16", "17"}:
            return EVIDENCE_ATTRIBUTED
        if chapter_number == "18":
            return EVIDENCE_HISTORICAL
        if chapter_number in {"19", "21", "22", "23", "24"}:
            return EVIDENCE_VERIFIED
        if chapter_number == "20":
            return EVIDENCE_POLICY
        if chapter_number == "27":
            if "fiyati ne kadar" in normalized_title:
                return EVIDENCE_UNKNOWN
            if "trendyol entegrasyonu" in normalized_title:
                return EVIDENCE_HISTORICAL
            if "hangi pazar yerleri" in normalized_title:
                return EVIDENCE_UNKNOWN
            if "verilerim guvende" in normalized_title or "google analytics" in normalized_title:
                return EVIDENCE_POLICY
            if "demo alabilir" in normalized_title:
                return EVIDENCE_PILOT
            return EVIDENCE_VISION
        if chapter_number in {"28", "29", "30", "31"}:
            return EVIDENCE_POLICY
        if chapter_number in {"4", "5"}:
            return EVIDENCE_VERIFIED
        if chapter_number in {"2", "3", "6", "7", "8", "9", "10", "11", "12", "25", "26", "32", "33"}:
            return EVIDENCE_VISION
        return EVIDENCE_VERIFIED

    @staticmethod
    def _answer_status(
        query: str,
        relevant: Sequence[KnowledgeSection],
        core: Optional[KnowledgeSection],
        intent: str,
        confidence: str,
    ) -> str:
        query_tokens = _tokens(query)
        normalized_query = _normalize(query)
        integration_aliases = TOPIC_ALIASES["entegrasyon"]
        unknown_platforms = integration_aliases - {"entegrasyon", "pazaryeri", "trendyol"}
        if _token_sets_overlap(query_tokens, unknown_platforms):
            return EVIDENCE_UNKNOWN
        if intent == INTENT_SUBSCRIPTION_PRICING:
            return EVIDENCE_UNKNOWN
        if intent == INTENT_SECURITY_PRIVACY:
            return EVIDENCE_POLICY
        if intent == INTENT_DEMO_CONTACT:
            return EVIDENCE_PILOT if "demo" in normalized_query else EVIDENCE_VERIFIED
        if intent == INTENT_COMPANY_INFORMATION and relevant:
            return relevant[0].evidence_status
        if intent in {INTENT_OUT_OF_SCOPE, INTENT_PROMPT_INJECTION}:
            return EVIDENCE_UNKNOWN
        if intent == INTENT_GREETING:
            return EVIDENCE_VERIFIED
        if confidence == "low":
            return EVIDENCE_UNKNOWN
        if relevant:
            return relevant[0].evidence_status
        if core is not None:
            return core.evidence_status
        return EVIDENCE_UNKNOWN

    @staticmethod
    def _format_with_budget(
        sections: Sequence[KnowledgeSection],
        max_chars: int,
    ) -> str:
        blocks: List[str] = []
        used = 0
        for section in sections:
            label, guidance = EVIDENCE_GUIDANCE[section.evidence_status]
            block = (
                f"### {section.title}\n"
                f"[KANIT STATÜSÜ: {label}]\n"
                f"[ZORUNLU DİL: {guidance}]\n"
                f"{section.content}"
            ).strip()
            separator_size = 2 if blocks else 0
            available = max_chars - used - separator_size
            if available <= 0:
                break
            if len(block) > available:
                if not blocks:
                    blocks.append(block[:available].rstrip())
                break
            blocks.append(block)
            used += len(block) + separator_size
        return "\n\n".join(blocks)
