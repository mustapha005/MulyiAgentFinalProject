from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from app.config import get_settings


@dataclass
class LLMResponse:
    content: str
    used_llm: bool
    error: Optional[str] = None


class OllamaLLMService:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.xai_api_key:
            raise ValueError("XAI_API_KEY is missing in .env")

        self.client = OpenAI(
            api_key=settings.xai_api_key,
            base_url=settings.grok_base_url,
            timeout=settings.llm_timeout_seconds,
        )

        self.model = settings.grok_model

    def generate(self, system_prompt: str, user_message: str) -> LLMResponse:
        try:
            print(f"[SmileFlow LLM] calling Grok model={self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )

            print("[SmileFlow LLM] Grok response received")

            return LLMResponse(
                content=response.choices[0].message.content or "",
                used_llm=True,
            )

        except Exception as exc:
            print(f"[SmileFlow LLM] Grok failed: {exc}")

            return LLMResponse(
                content="",
                used_llm=False,
                error=str(exc),
            )


def get_llm_service() -> Optional[OllamaLLMService]:
    settings = get_settings()

    if settings.llm_provider.lower() != "grok":
        return None

    return OllamaLLMService()