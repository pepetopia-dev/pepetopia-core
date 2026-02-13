import os
import logging
import asyncio
from google import genai
from google.genai import types
from .app_config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Centralized service for interacting with Google Gemini API.
    """
    
    @staticmethod
    async def _generate_with_retry(prompt: str, system_instruction: str, retries: int = 3) -> tuple[str, str]:
        """
        Generates content using Gemini with retry logic for transient errors.
        Returns a tuple: (response_text, model_name)
        """
        
        # API Key kontrolü
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing.")
            return "⚠️ Error: API Key missing.", "unknown-model"

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        model_id = "gemini-2.0-flash"  # Veya 'gemini-1.5-pro-latest' kullanabilirsiniz

        for attempt in range(retries):
            try:
                # API Çağrısı
                response = await client.aio.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                        max_output_tokens=1000,
                        response_mime_type="application/json" # JSON zorunluluğu için
                    )
                )

                if response.text:
                    return response.text, model_id
                else:
                    logger.warning(f"Attempt {attempt + 1}: Empty response from Gemini.")

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if "429" in str(e):  # Rate limit hatası
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    await asyncio.sleep(1)
        
        logger.error("All attempts to contact Gemini failed.")
        return "⚠️ Error: AI Service Unavailable.", model_id