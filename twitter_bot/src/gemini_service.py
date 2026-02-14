import logging
import asyncio
import re
from google import genai
from google.genai import types
from .app_config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Centralized service for interacting with Google Gemini API.
    
    POLICY:
    - NO HARDCODED MODEL NAMES.
    - Fully dynamic discovery via API.
    - Regex-based version sorting (Newest first).
    """
    
    # Cache to prevent fetching models on every single request
    _model_cache = []

    @staticmethod
    async def _get_sorted_models(client):
        """
        Discovers all available 'generateContent' models and sorts them by version.
        Sort Logic: Extracts version number via Regex and sorts Descending.
        """
        # Return cached list if available and not empty
        if GeminiService._model_cache:
            return GeminiService._model_cache

        logger.info("📡 Contacting Google API to fetch available model list...")
        found_models = []

        try:
            # Google GenAI SDK v0.7+ async iterator for listing models
            async for model in client.aio.models.list():
                # Filter 1: Must be a 'gemini' model
                # Filter 2: Must support 'generateContent' method
                if "gemini" in model.name.lower() and "generateContent" in model.supported_generation_methods:
                    # Clean up the name (some return as 'models/gemini-pro')
                    clean_name = model.name.replace("models/", "")
                    found_models.append(clean_name)
            
            if not found_models:
                logger.critical("❌ API returned 0 Gemini models! Please check API Key permissions or Region availability.")
                return []

            # --- REGEX BASED VERSION SORTING ---
            def version_scorer(name):
                # Extracts version numbers like 1.5, 2.0, 1.0
                # Matches "gemini-1.5" or "gemini-2.0"
                match = re.search(r'gemini-(\d+(?:\.\d+)?)', name, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                return 0.0 # If no version number found, push to bottom

            # Sort descending: Highest version number first (e.g. 2.0 > 1.5)
            # If versions are same, secondary sort isn't strictly needed but 'latest' usually implies newer.
            sorted_models = sorted(found_models, key=version_scorer, reverse=True)

            GeminiService._model_cache = sorted_models
            logger.info(f"✅ Discovered & Sorted Models: {sorted_models}")
            return sorted_models

        except Exception as e:
            logger.error(f"🔥 Critical Error during model discovery: {e}")
            # STRICT RULE: Do NOT return a hardcoded list here.
            # If discovery fails, we simply cannot proceed.
            return []

    @staticmethod
    async def _generate_with_retry(prompt: str, system_instruction: str, retries: int = 3) -> tuple[str, str]:
        """
        Generates content by iterating through the dynamically discovered list.
        """
        
        if not Config.GEMINI_API_KEY:
            logger.error("Gemini API Key is missing.")
            return "⚠️ Error: API Key missing.", "unknown-model"

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # 1. Fetch Dynamic List (No hardcoded fallback)
        models_to_try = await GeminiService._get_sorted_models(client)
        
        if not models_to_try:
            return "⚠️ System Error: No AI models could be discovered from Google API.", "None"

        last_error = None

        # 2. Iterate through the discovered models
        for model_id in models_to_try:
            
            # Retry logic for the SAME model (for transient network blips)
            for attempt in range(retries):
                try:
                    logger.info(f"🤖 Generating with {model_id} (Attempt {attempt+1})")
                    
                    response = await client.aio.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                            # Safety check: ensure max tokens is reasonable
                            max_output_tokens=1000, 
                            response_mime_type="application/json"
                        )
                    )

                    if response.text:
                        return response.text, model_id
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    
                    # --- SMART SWITCHING LOGIC ---
                    
                    # If Rate Limit (429) OR Not Found (404) -> STOP trying this model, GO TO NEXT.
                    # 404 can happen if the API list returns a model that your specific API Key tier can't access.
                    if any(err_code in error_msg for err_code in ["429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND"]):
                        logger.warning(f"🚫 {model_id} unavailable ({error_msg}). Switching to next model...")
                        break # Breaks inner retry loop, continues outer model loop
                    
                    # For other errors (500, timeout), wait and retry the SAME model
                    logger.warning(f"⚠️ Transient error on {model_id}: {error_msg}. Retrying...")
                    await asyncio.sleep(1 + attempt)
            
        logger.error(f"💀 All discovered models failed. Last error: {last_error}")
        return "⚠️ Error: All available AI models failed to respond.", "None"