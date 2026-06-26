"""
LLM Client
==========
OpenRouter/OpenAI Client for communicating with the LLM
"""

import json
from typing import Any, Dict, Optional
from openai import AsyncOpenAI
from loguru import logger

from core.config import settings
from core.exceptions import LLMException


class LLMClient:
    """Client for communicating with the OpenRouter API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.BASE_URL,
            timeout=settings.LLM_TIMEOUT
        )
        self.model = settings.MODEL_NAME
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text using LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Creativity level (0-1)
            max_tokens: Maximum response tokens
            response_format: JSON schema for structured output
            
        Returns:
            Generated text
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            logger.debug(f"🤖 Sending request to LLM: {self.model}")
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add response format if provided (for JSON mode)
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            logger.debug(f"✅ LLM response received: {len(content)} chars")
            
            return content
            
        except Exception as e:
            logger.error(f"❌ LLM error: {str(e)}")
            raise LLMException(
                message=f"LLM generation failed: {str(e)}",
                details={"model": self.model, "error": str(e)}
            )
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Lower for more consistent JSON
            
        Returns:
            Parsed JSON dict
        """
        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON
            result = json.loads(response)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {str(e)}")
            raise LLMException(
                message="Failed to parse LLM response as JSON",
                details={"error": str(e), "response": response[:500]}
            )


# Singleton instance
llm_client = LLMClient()
