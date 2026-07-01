"""
LLM Client Module
=================
Unified LLM client for Groq API (OpenAI-compatible)
"""

import json
import re
from typing import Any, Dict, Optional

from openai import AsyncOpenAI
from loguru import logger

from core.config import settings
from core.exceptions import LLMException


class LLMClient:
    """Async LLM client wrapping Groq's OpenAI-compatible API"""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
            max_retries=settings.LLM_MAX_RETRIES,
        )
        self._model = settings.GROQ_MODEL

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate raw text from the LLM"""
        try:
            kwargs: Dict[str, Any] = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens

            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMException(
                message=f"LLM generation failed: {str(e)}",
                details={"model": self._model},
            )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """Generate JSON output from the LLM"""
        raw = await self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Parse JSON from raw LLM output, handling markdown fences"""
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        return json.loads(cleaned)


# Singleton instance
llm_client = LLMClient()
