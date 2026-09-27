"""Load the complete Yosuun knowledge document for simple RAG."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class KnowledgeSourceError(RuntimeError):
    """Raised when the knowledge document cannot be loaded safely."""


class KnowledgeService:
    """Read and cache one complete Markdown knowledge document."""

    def __init__(self, source_path: Path) -> None:
        self.source_path = Path(source_path)
        self._content: Optional[str] = None

    def read_all(self) -> str:
        """Return the full document without chunking, ranking or intent logic."""

        if self._content is None:
            try:
                content = self.source_path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise KnowledgeSourceError(
                    f"Yosuun bilgi kaynağı okunamadı: {self.source_path}"
                ) from exc
            if not content:
                raise KnowledgeSourceError("Yosuun bilgi kaynağı boş olamaz.")
            self._content = content
        return self._content
