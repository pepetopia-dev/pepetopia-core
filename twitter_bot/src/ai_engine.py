import google.generativeai as genai
from google.api_core import exceptions
import logging
import re
from src.app_config import Config

logger = logging.getLogger(__name__)

# --- SYSTEM PROMPT (X ALGORITHM GENERATOR) ---
SYSTEM_PROMPT = """
You are an expert X (Twitter) Algorithm Engineer for 'Pepetopia'.
Your Goal: Generate 3 DISTINCT high-ranking reply options for the input tweet.

--- ALGORITHM RULES (INTERNAL) ---
1. Reply Weight (75x): High priority on questions to trigger back-and-forth.
2. Media Richness: Suggest visual formats (Video/Image) to boost 'dwell time'.
3. SimClusters: Use keywords relevant to the tweet's topic (Software/Finance/Crypto).
4. Safety: ZERO toxicity.
5. NO LINKS.

--- OUTPUT FORMAT (STRICT) ---
You must provide 3 options (Variations).
For the '📋 COPY:' section, use PLAIN TEXT only (No markdown, no bold, no italics).

Option 1: [Define Strategy: e.g., Witty/Humorous]
Score: [0-100] (Reasoning: e.g., High Reply Weight due to question)
Media: [Suggest Image/Video/None]
📋 COPY:
[Write the tweet here - Plain Text]

Option 2: [Define Strategy: e.g., Insightful/Supportive]
Score: [0-100]
Media: [Suggest Image/Video/None]
📋 COPY:
[Write the tweet here - Plain Text]

Option 3: [Define Strategy: e.g., Provocative/Debate]
Score: [0-100]
Media: [Suggest Image/Video/None]
📋 COPY:
[Write the tweet here - Plain Text]
"""

class ModelManager:
    """
    Manages dynamic discovery, fallback logic, and 'Sticky' model selection.
    """
    _cached_models = []
    _current_index = 0  # Points to the last known working model

    @staticmethod
    def _extract_version(model_name: str) -> float:
        """
        Extracts version number for sorting. 
        Supports both '1.5' (float) and '3' (int) formats.
        """
        match = re.search(r'(\d+(?:\.\d+)?)', model_name)
        if match:
            return float(match.group(1))
        return 0.0

    @classmethod
    def get_prioritized_models(cls):
        """
        Fetches models from Google, filters for 'generateContent', 
        and sorts by Version (Newest First) -> Name.
        """
        if cls._cached_models:
            return cls._cached_models

        try:
            logger.info("📡 Discovering available Gemini models...")
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            all_models = list(genai.list_models())
            valid_models = []

            for m in all_models:
                if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                    valid_models.append(m.name)
            
            # Sort by version descending (e.g., 3.0 > 2.0 > 1.5)
            # Second sort key prefers 'pro' models over 'flash' for same versions
            valid_models.sort(key=lambda x: (cls._extract_version(x), 'pro' in x), reverse=True)
            
            if not valid_models:
                logger.warning("⚠️ No models found dynamically. Using hardcoded fallback.")
                # Fallback list
                valid_models = ["models/gemini-1.5-pro", "models/gemini-1.5-flash"]

            logger.info(f"✅ Model Priority List: {valid_models}")
            cls._cached_models = valid_models
            return valid_models

        except Exception as e:
            logger.error(f"❌ Model discovery failed: {e}")
            return ["models/gemini-1.5-flash"]

    @classmethod
    def update_champion(cls, model_name):
        """Updates the pointer to the current working model."""
        if model_name in cls._cached_models:
            cls._current_index = cls._cached_models.index(model_name)

    @classmethod
    def get_rotated_list(cls):
        """
        Returns the model list but rotated so it STARTS with the last working model.
        Example: [A, B, C, D] with index 2 becomes [C, D, A, B]
        """
        models = cls.get_prioritized_models()
        if not models:
            return []
            
        # Safety check for index bounds
        if cls._current_index >= len(models):
            cls._current_index = 0
            
        # Slice and rotate
        return models[cls._current_index:] + models[:cls._current_index]

def analyze_and_draft(user_input: str) -> str:
    """
    Tries to generate content using the best available model.
    Uses 'Sticky Session' logic: Starts from the last working model.
    """
    # Get the list starting from our current champion
    candidate_models = ModelManager.get_rotated_list()
    
    final_prompt = f"""
    Target Tweet:
    "{user_input}"
    
    Task: Generate 3 High-Ranking Reply Options based on X Algorithm.
    """

    for model_name in candidate_models:
        try:
            # logger.info(f"🧠 Trying Engine: {model_name}") 
            
            model = genai.GenerativeModel(
                model_name, 
                system_instruction=SYSTEM_PROMPT
            )
            
            response = model.generate_content(final_prompt)
            result = response.text.strip()
            
            # SUCCESS!
            # 1. Update the sticky pointer so next time we start here.
            ModelManager.update_champion(model_name)
            
            # 2. Append Footer
            result += f"\n\n⚙️ *Engine: {model_name.replace('models/', '')}*"
            return result

        except exceptions.ResourceExhausted:
            logger.warning(f"⚠️ Quota Exceeded for {model_name}. Switching...")
            continue
            
        except Exception as e:
            logger.error(f"❌ Error with {model_name}: {e}. Switching...")
            continue

    return "🚫 CRITICAL ERROR: All AI models failed."