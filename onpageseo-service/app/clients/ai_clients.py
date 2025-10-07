# onpageseo/app/clients/ai_clients.py

import logging
import httpx
from ..core.config import get_settings
import json  # <-- needed
import re

settings = get_settings()


class AIClient:
    """
    Wrapper around Gemini AI model.
    Strictly locked to Gemini only.
    """

    def __init__(self):
# In ai_clients.py
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"       
        self.gemini_key = settings.gemini_api_key  # ✅ must set GEMINI_API_KEY in .env
        self.serpapi_key = settings.serpapi_key    # ✅ SERPAPI_KEY optional
        self.ahrefs_key = settings.ahrefs_key      # ✅ AHREFS_KEY optional

        if not self.gemini_key:
            raise RuntimeError("GEMINI_API_KEY must be set in environment")

    async def generate(self, prompt: str) -> str:
        """Generate text using Gemini with correct API format."""
        print(f"🤖 [GENERATE] Sending prompt to Gemini (length: {len(prompt)})")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.gemini_url}?key={self.gemini_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.1,  # Lower for more deterministic results
                            "maxOutputTokens": 2048,
                            "responseMimeType": "text/plain"
                        }
                    },
                    headers={
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"🤖 [GENERATE] Gemini response status: {response.status_code}")
                
                response.raise_for_status()
                data = response.json()
                
                # ✅ Correct response parsing for Gemini API
                if "candidates" in data and data["candidates"]:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text = candidate["content"]["parts"][0].get("text", "")
                        print(f"🤖 [GENERATE] Received response (length: {len(text)})")
                        return text
                
                print("🤖 [GENERATE] No valid content in Gemini response")
                return ""
                
        except httpx.HTTPStatusError as e:
            print(f"🤖 [GENERATE] HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Gemini API error: {e.response.status_code}")
        except Exception as e:
            print(f"🤖 [GENERATE] Unexpected error: {str(e)}")
            raise RuntimeError(f"Gemini request failed: {str(e)}")

    async def generate_structured(self, prompt: str):
        """
        Generate structured JSON. Always returns a dict or list.
        Never raw strings.
        """
        print("🤖 [STRUCTURED] Generating structured JSON response")
        
        # Force Gemini to respond in JSON
        json_prompt = f"""{prompt}

        IMPORTANT: Return ONLY valid JSON. 
        No text outside of JSON. No markdown. No explanations.
        """
        
        text = await self.generate(json_prompt)
        
        try:
            # Extract JSON block if surrounded by text
            json_match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                print("🤖 [STRUCTURED] Successfully parsed JSON response")
                return result

            # Direct parsing
            result = json.loads(text)
            print("🤖 [STRUCTURED] Successfully parsed direct JSON response")
            return result

        except Exception as e:
            print(f"🤖 [STRUCTURED] JSON parsing failed: {str(e)}")
            print(f"🤖 [STRUCTURED] Raw response (first 200 chars): {text[:200]}")
            # 🔥 Instead of returning {"raw_output": ...}, 
            # return a valid empty structure that won't break other files
            return {}  # Always dict, safe for downstream usage



# ✅ Always point everything to the same Gemini client
gemini_client = AIClient()
ai_client = gemini_client

# Aliases so legacy code doesn’t break
openai_client = gemini_client
claude_client = gemini_client
mistral_client = gemini_client
