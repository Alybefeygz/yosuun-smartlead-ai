"""Local retrieval for the curated Yosuun Markdown knowledge base."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Sequence, Set


HEADING_PATTERN = re.compile(r"^(#{1,2})\s+(.+?)\s*$")
TOP_LEVEL_NUMBER_PATTERN = re.compile(r"^(\d+)\.")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# These chapters contain authoring instructions rather than visitor-facing facts.
RETRIEVAL_EXCLUDED_CHAPTERS = frozenset({"1", "34", "35", "36", "37", "38"})

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
    "rakip": {"analiz", "karsilastirma", "rakip", "takip"},
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
    normalized_title: str
    normalized_content: str


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

    def __init__(self, source_path: Path) -> None:
        self.source_path = Path(source_path)
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

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Bilgi arama sorgusu boş olmayan bir metin olmalıdır.")
        if max_sections <= 0 or max_chars <= 0:
            raise ValueError("Bilgi arama limitleri pozitif olmalıdır.")

        query_tokens = _expanded_query_tokens(query)
        normalized_query = _normalize(query)
        ranked = sorted(
            (
                (self._score(section, query_tokens, normalized_query), section)
                for section in self.sections
            ),
            key=lambda item: (-item[0], item[1].order),
        )

        selected: List[KnowledgeSection] = []
        core = self._core_section()
        if core is not None:
            selected.append(core)

        for score, section in ranked:
            if score <= 0 or section in selected:
                continue
            selected.append(section)
            if len(selected) >= max_sections:
                break

        return self._format_with_budget(selected, max_chars)

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
    ) -> int:
        title_tokens = set(section.normalized_title.split())
        content_tokens = set(section.normalized_content.split())
        score = 0
        for token in query_tokens:
            if KnowledgeService._has_related_token(token, title_tokens):
                score += 8
            elif KnowledgeService._has_related_token(token, content_tokens):
                score += 2
        if len(normalized_query) >= 5 and normalized_query in section.normalized_content:
            score += 12
        return score

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
    def _format_with_budget(
        sections: Sequence[KnowledgeSection],
        max_chars: int,
    ) -> str:
        blocks: List[str] = []
        used = 0
        for section in sections:
            block = f"### {section.title}\n{section.content}".strip()
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
