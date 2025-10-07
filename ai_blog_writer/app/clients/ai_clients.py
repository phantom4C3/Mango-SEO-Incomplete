# ai_blog_writer/src/app/services/ai_clients.py
import httpx
import json
import re
from typing import Optional

from ..middleware.rate_limiter import ai_rate_limit
from ..core.config import settings
from google import genai
from typing import Optional 


class NanoBananaClient:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def generate_image(self, prompt: str, image: Optional[bytes] = None):
        response = await self.client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt, image] if image else [prompt],
        )
        return response


# Instantiate a singleton Nano client
nano_banana_client = NanoBananaClient(api_key=settings.gemini_nano_api_key)


class GeminiClient:
    """
    Async client for Google Gemini (Gen AI) API.
    Only Gemini is supported in AI Blog Writer.
    """

    def __init__(self, api_key: str):
        self.gemini_key = api_key
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

        if not self.gemini_key:
            raise RuntimeError("GEMINI_API_KEY must be set in environment")

    @ai_rate_limit(provider="gemini", max_requests=60, window_seconds=60)
    async def generate(self, prompt: str, user_id: Optional[str] = None) -> str:
        """
        Generate text using Gemini.
        Args:
            prompt: text prompt to send
            user_id: optional user_id for Redis rate limiting
        Returns:
            Generated text string
        """
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.gemini_url}?key={self.gemini_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2048,
                        "responseMimeType": "text/plain",
                    },
                },
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            data = response.json()

            # Parse Gemini response (robust version from onpageseo)
            if "candidates" in data and data["candidates"]:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    return text


            return ""

    @ai_rate_limit(provider="gemini", max_requests=30, window_seconds=60)
    async def generate_structured(
        self, prompt: str, user_id: Optional[str] = None
    ) -> dict:
        """
        Generate structured JSON output from Gemini.
        Always returns a dict (safe for downstream usage).
        """
        json_prompt = f"""
        {prompt}

        IMPORTANT: Return ONLY valid JSON. 
        No text outside JSON. No markdown. No explanations.
        """

        text = await self.generate(json_prompt, user_id=user_id)

        # Attempt to parse JSON from response
        try:
            json_match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(text)
        except Exception:
            # Fail-safe: return empty dict
            return {}


# Instantiate a single global Gemini client
gemini_client = GeminiClient(api_key=settings.gemini_api_key)
