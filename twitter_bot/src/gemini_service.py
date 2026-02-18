import logging
import asyncio
import re
from typing import List, Optional, Dict, Any
from google import genai
from google.genai import types
from .app_config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Centralized service for interacting with Google Gemini API.
    
    POLICY:
    - NO HARDCODED MODEL NAMES (dynamically discovered).
    - Exception: A known good fallback is used if discovery fails.
    - Regex-based version sorting (Newest first).
    """
    
    # Cache to prevent fetching models on every single request
    _model_cache: List[str] = []
    
    # SAFE FALLBACK: If API discovery fails entirely, default to a known stable model.
    # This ensures the bot doesn't crash even if the list endpoint is flaky.
    _FALLBACK_MODEL = "gemini-1.5-flash"

    @staticmethod
    def _extract_version(name: str) -> float:
        """
        Extracts version number for sorting.
        e.g. 'gemini-1.5-flash' -> 1.5
        e.g. 'gemini-2.0-flash-exp' -> 2.0
        """
        match = re.search(r'gemini-(\d+(?:\.\d+)?)', name, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0

    @staticmethod
    async def list_models(client: genai.Client) -> List[str]:
        """
        Discovers all available 'generateContent' models and sorts them by version.
        Uses caching to reduce latency.
        """
        # Return cached list if available and not empty
        if GeminiService._model_cache:
            return GeminiService._model_cache

        logger.info("📡 Contacting Google API to fetch available model list...")
        found_models = []

        try:
            # FIX: 'client.aio.models.list()' is a coroutine
            models_response = await client.aio.models.list()
            
            # Iterate through the response object
            for model in models_response:
                # Filter 1: Must be a 'gemini' model
                # Filter 2: Must support 'generateContent' method
                if "gemini" in model.name.lower() and "generateContent" in model.supported_generation_methods:
                    # Clean up the name (some return as 'models/gemini-pro')
                    clean_name = model.name.replace("models/", "")
                    found_models.append(clean_name)
            
            if not found_models:
                logger.warning("⚠️ API returned 0 Gemini models! Check API Key permissions.")
                # We do NOT return fallback here, just empty list. 
                # Caller (select_newest_model) handles fallback.
                return []

            # Sort descending: Highest version number first (e.g. 2.0 > 1.5)
            # Deterministic ordering: Version desc, then Name asc (for stability if versions tie)
            found_models.sort(key=lambda x: (GeminiService._extract_version(x), x), reverse=True)

            GeminiService._model_cache = found_models
            logger.info(f"✅ Discovered & Sorted Models: {found_models}")
            return found_models

        except Exception as e:
            logger.error(f"🔥 Critical Error during model discovery: {e}")
            # Return empty list to trigger fallback in caller
            return []

    @staticmethod
    async def select_newest_model(client: genai.Client, preference_rules: Optional[Dict[str, Any]] = None) -> str:
        """
        Selects the best available model based on version and rules.
        If discovery fails, returns the safe fallback.
        """
        candidates = await GeminiService.list_models(client)
        
        if not candidates:
            logger.warning(f"⚠️ Model discovery failed. Using fallback: {GeminiService._FALLBACK_MODEL}")
            return GeminiService._FALLBACK_MODEL
        
        # Apply preference rules if any (currently just picking top sorted)
        # Verify "stable" preference if requested?
        # For now, our sort logic (Version Desc) + standard stable > experimental naming conventions usually works.
        
        # Simple selection: The first one (highest version)
        best_model = candidates[0]
        
        # Optional: Log if we are picking an experimental model?
        if "exp" in best_model.lower() or "preview" in best_model.lower():
             logger.info(f"ℹ️ Selected newest model (experimental/preview): {best_model}")
        else:
             logger.info(f"ℹ️ Selected newest model (stable): {best_model}")
             
        return best_model

    @staticmethod
    async def _generate_with_retry(prompt: str, system_instruction: str, retries: int = 3) -> tuple[str, str]:
        """
        Generates content using the newest discovered model.
        Falls back to other models/retries if generation fails.
        """
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing.")
            return "⚠️ Error: API Key missing.", "unknown-model"

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # 1. Select the primary model
        primary_model = await GeminiService.select_newest_model(client)
        
        # List of models to try in order.
        # Primary first, then maybe fallback if primary isn't the fallback.
        models_to_try = [primary_model]
        
        # If the primary model fails (and isn't the fallback), we try the fallback.
        if primary_model != GeminiService._FALLBACK_MODEL:
             models_to_try.append(GeminiService._FALLBACK_MODEL)
             
        last_error = None

        for model_id in models_to_try:
            # Avoid trying the same model twice if list has duplicates
            
            for attempt in range(retries):
                try:
                    logger.info(f"🤖 Generating with {model_id} (Attempt {attempt+1})")
                    
                    response = await client.aio.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                            max_output_tokens=1000, 
                            response_mime_type="application/json"
                        )
                    )

                    if response.text:
                        return response.text, model_id
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    
                    # Smart Switching Logic
                    # If Rate Limit (429) or Not Found (404), switch immediately.
                    if any(err_code in error_msg for err_code in ["429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND"]):
                        logger.warning(f"🚫 {model_id} unavailable ({error_msg}). Switching/Retrying...")
                        break # Break inner retry loop, go to next model
                    
                    # For other errors (500), wait and retry same model
                    logger.warning(f"⚠️ Transient error on {model_id}: {error_msg}. Retrying...")
                    await asyncio.sleep(1 + attempt)
            
            # If we are here, the model failed all retries or broke out.
            # Continue to next model in list.
            
        logger.error(f"💀 All attempted models failed. Last error: {last_error}")
        return "⚠️ Error: All available AI models failed to respond.", "None"
