"""Groq integration boundary for Yosuun AI responses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from config import Config


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
ALLOWED_HISTORY_ROLES = frozenset({"user", "assistant"})
DEMO_MODE_RESPONSE = (
    "Yosuun AI Asistan şu anda demo modunda çalışıyor. "
    "Yosuun'un e-ticaret operasyonlarınıza nasıl yardımcı olabileceğini "
    "görüşmek için iletişim formunu doldurabilirsiniz."
)
_UNSET = object()


class AIServiceError(RuntimeError):
    """Normalized external AI provider failure."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "groq",
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class AIService:
    """Build prompts, call Groq and normalize its response."""

    def __init__(
        self,
        *,
        api_key: Any = _UNSET,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        business_context: Optional[str] = None,
        max_history_messages: Optional[int] = None,
        max_history_chars: Optional[int] = None,
    ) -> None:
        configured_api_key = Config.GROQ_API_KEY if api_key is _UNSET else api_key
        self.api_key = (
            configured_api_key.strip()
            if isinstance(configured_api_key, str) and configured_api_key.strip()
            else None
        )
        selected_provider = Config.AI_PROVIDER if provider is None else provider
        selected_model = Config.GROQ_MODEL if model is None else model
        selected_context = (
            Config.BUSINESS_CONTEXT if business_context is None else business_context
        )
        self.provider = selected_provider.strip().lower()
        self.model = selected_model.strip()
        self.timeout = Config.AI_TIMEOUT_SECONDS if timeout is None else timeout
        self.business_context = selected_context.strip()
        self.max_history_messages = (
            Config.AI_HISTORY_MAX_MESSAGES
            if max_history_messages is None
            else max_history_messages
        )
        self.max_history_chars = (
            Config.AI_HISTORY_MAX_CHARS
            if max_history_chars is None
            else max_history_chars
        )

        if self.timeout <= 0:
            raise ValueError("AI timeout pozitif olmalıdır.")
        if self.max_history_messages <= 0 or self.max_history_chars <= 0:
            raise ValueError("AI geçmiş limitleri pozitif olmalıdır.")
        if not self.business_context:
            raise ValueError("BUSINESS_CONTEXT boş olamaz.")
        if not self.model:
            raise ValueError("AI model adı boş olamaz.")

    def yanit_uret(
        self,
        mesaj: str,
        gecmis: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Return a normalized assistant response for one user message."""

        messages = self._build_messages(mesaj, gecmis)
        if not self.api_key:
            return DEMO_MODE_RESPONSE
        return self._call_provider(messages)

    def _build_messages(
        self,
        mesaj: str,
        gecmis: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """Build system, bounded history and current-user messages in order."""

        if not isinstance(mesaj, str) or not mesaj.strip():
            raise ValueError("Mesaj boş olmayan bir metin olmalıdır.")

        validated_history = self._validate_and_limit_history(gecmis)
        return [
            {"role": "system", "content": self.business_context},
            *validated_history,
            {"role": "user", "content": mesaj.strip()},
        ]

    def _validate_and_limit_history(
        self,
        gecmis: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        """Validate frontend history and apply count and character budgets."""

        if gecmis is None:
            return []
        if not isinstance(gecmis, list):
            raise ValueError("Sohbet geçmişi bir liste olmalıdır.")

        normalized_history: List[Dict[str, str]] = []
        for index, item in enumerate(gecmis):
            if not isinstance(item, dict):
                raise ValueError(f"Geçmiş kaydı {index} bir nesne olmalıdır.")

            role = item.get("role")
            content = item.get("content")
            if role not in ALLOWED_HISTORY_ROLES:
                raise ValueError("Geçmişte yalnızca user ve assistant rolleri kullanılabilir.")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Geçmiş mesaj içeriği boş olmayan bir metin olmalıdır.")

            normalized_history.append(
                {"role": role, "content": content.strip()}
            )

        count_limited = normalized_history[-self.max_history_messages :]
        selected_reversed: List[Dict[str, str]] = []
        used_characters = 0
        for item in reversed(count_limited):
            message_size = len(item["content"])
            if used_characters + message_size > self.max_history_chars:
                break
            selected_reversed.append(item)
            used_characters += message_size

        return list(reversed(selected_reversed))

    def _call_provider(self, messages: List[Dict[str, str]]) -> str:
        """Call Groq with a finite timeout and parse one assistant response."""

        if self.provider != "groq":
            raise AIServiceError(
                "Yapılandırılan AI sağlayıcısı desteklenmiyor.",
                provider=self.provider,
            )

        try:
            response = requests.post(
                GROQ_CHAT_COMPLETIONS_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise AIServiceError(
                "AI sağlayıcısı zaman aşımına uğradı.",
                provider=self.provider,
            ) from exc
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            raise AIServiceError(
                "AI sağlayıcısı başarısız bir HTTP cevabı döndürdü.",
                provider=self.provider,
                status_code=status_code,
            ) from exc
        except requests.RequestException as exc:
            raise AIServiceError(
                "AI sağlayıcısına ulaşılamadı.",
                provider=self.provider,
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AIServiceError(
                "AI sağlayıcısı geçersiz JSON döndürdü.",
                provider=self.provider,
                status_code=response.status_code,
            ) from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIServiceError(
                "AI sağlayıcısı cevabı beklenen formatta değil.",
                provider=self.provider,
                status_code=response.status_code,
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise AIServiceError(
                "AI sağlayıcısı boş cevap döndürdü.",
                provider=self.provider,
                status_code=response.status_code,
            )
        return content.strip()


ai_service = AIService()
