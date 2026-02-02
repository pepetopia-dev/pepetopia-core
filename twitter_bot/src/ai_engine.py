from google import genai
from google.genai import types
import logging
import re
import json
from src.app_config import Config
from src.utils import extract_url_content

logger = logging.getLogger(__name__)

# --- 1. X ALGORITHM RULES ---
X_ALGO_RULES = """
--- X ALGORITHM OPTIMIZATION RULES ---
Your output MUST maximize these internal scoring variables:
1. REPLY_WEIGHT: Provoke debates or ask high-signal questions.
2. PROFILE_CLICK_WEIGHT: Create "Curiosity Gaps".
3. PHOTO_EXPAND_WEIGHT: Reference visual data.
4. DWELL_TIME: Use high-value, dense information.
5. VQV_WEIGHT: Mention video/animation context if applicable.
"""

# --- 2. PERSONA DEFINITIONS ---
PERSONAS = {
    "dev": {
        "role": "THE ARCHITECT (@pepetopia_dev)",
        "tone": "Solution-Oriented, Transparent, 'Builder-to-Builder', Analytical.",
        "goals": "Build trust through technical competence. NO SHILLING.",
        "style_guide": "Focus on architecture, logic, and solutions. Avoid specific syntax unless asked.",
        "drift_guard": "STAY ON TOPIC. Do not pivot to random tech stacks."
    },
    "brand": {
        "role": "THE VISIONARY (@pepetopia)",
        "tone": "High-Status, Intellectual, 'The Insider', Commanding.",
        "goals": "Dominate the narrative. Frame Pepetopia as the inevitable future.",
        "style_guide": "Focus on 'Why' and 'Macro Impact'. Talk about Freedom and Dominance.",
        "drift_guard": "STAY ON TOPIC. Connect the input to the ecosystem vision."
    }
}

class StrategyEngine:
    @staticmethod
    def construct_adaptive_prompt(user_input: str, persona_key: str) -> str:
        persona = PERSONAS.get(persona_key, PERSONAS["brand"])
        return f"""
--- IDENTITY PROTOCOL: {persona['role']} ---
Tone: {persona['tone']}
Goal: {persona['goals']}
Constraint: {persona['drift_guard']}

{X_ALGO_RULES}

--- INPUT CONTEXT ---
"{user_input}"

--- MISSION ---
Generate 3 HIGH-RANKING tweet options acting strictly as {persona['role']}.
CRITICAL: Stick to the subject matter of the INPUT CONTEXT.

--- OUTPUT FORMAT (JSON ONLY) ---
Output purely valid JSON. No markdown.
{{
  "analysis_summary": "Brief analysis.",
  "options": [
    {{
      "strategy_mode": "MODE_NAME",
      "target_metric": "ALGO_VARIABLE",
      "score_prediction": 95,
      "visual_cue": "Description.",
      "tweet_content": "Content here. End with #{'PepetopiaDev' if persona_key == 'dev' else 'Pepetopia'}."
    }}
  ]
}}
"""

class ModelManager:
    """
    Manages DYNAMIC discovery and fallback logic.
    Restored to fetch live models from Google and sort by power.
    """
    _client = None
    _cached_models = []
    _current_index = 0

    @classmethod
    def get_client(cls):
        if not cls._client:
            cls._client = genai.Client(api_key=Config.GEMINI_API_KEY)
        return cls._client

    @staticmethod
    def _model_sort_key(model_name: str):
        """
        Sorting Logic:
        1. Version Number (Higher is better, e.g., 2.0 > 1.5)
        2. Tier (Pro > Flash > Nano)
        """
        # Extract version (default to 0 if not found)
        version_match = re.search(r'(\d+(?:\.\d+)?)', model_name)
        version = float(version_match.group(1)) if version_match else 0.0
        
        # Tier priority
        tier_score = 0
        if 'pro' in model_name: tier_score = 3
        elif 'flash' in model_name: tier_score = 2
        elif 'nano' in model_name: tier_score = 1
        
        return (version, tier_score)

    @classmethod
    def get_rotated_list(cls):
        """
        Fetches LIVE models from API, filters for Gemini, sorts by power,
        and rotates based on the last working model (Sticky Session).
        """
        if not cls._cached_models:
            try:
                client = cls.get_client()
                logger.info("📡 Dynamically discovering Gemini models...")
                
                # Fetch all models
                # In new SDK, we iterate over the paginated list
                found_models = []
                for m in client.models.list():
                    # Filter for 'gemini' and ensure it's a generation model
                    # Note: New SDK model objects might differ, checking name is safest
                    if 'gemini' in m.name.lower() and 'vision' not in m.name.lower():
                        # Clean the name (remove 'models/' prefix if present for clean ID)
                        clean_name = m.name.replace('models/', '')
                        found_models.append(clean_name)

                if not found_models:
                    logger.warning("⚠️ No models found via API. Using emergency fallback.")
                    found_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
                
                # Sort descending (Best first)
                found_models.sort(key=cls._model_sort_key, reverse=True)
                
                # Deduplicate just in case
                cls._cached_models = list(dict.fromkeys(found_models))
                logger.info(f"✅ Dynamic Model Chain: {cls._cached_models}")
                
            except Exception as e:
                logger.error(f"❌ Dynamic discovery failed: {e}")
                # Emergency hardcoded list if API discovery fails completely
                return ["gemini-1.5-flash"]

        # Rotate list: [Current, Next, ..., Previous]
        if cls._current_index >= len(cls._cached_models):
            cls._current_index = 0
            
        return cls._cached_models[cls._current_index:] + cls._cached_models[:cls._current_index]

    @classmethod
    def update_champion(cls, model_name):
        """Locks onto the successful model to prevent unnecessary switching."""
        if model_name in cls._cached_models:
            cls._current_index = cls._cached_models.index(model_name)

def analyze_and_draft(user_input: str) -> str:
    # 1. ROUTING
    persona_key = "brand"
    clean_input = user_input
    match = re.search(r'(@pepetopia_dev|@pepetopia)\s*$', user_input, re.IGNORECASE)
    if match:
        tag = match.group(1).lower()
        persona_key = "dev" if "dev" in tag else "brand"
        clean_input = user_input[:match.start()].strip()

    # 2. ENRICHMENT & SANITIZATION
    enriched_input = extract_url_content(clean_input)
    sanitized_input = enriched_input[:2000]

    # 3. GENERATION
    candidate_models = ModelManager.get_rotated_list()
    final_prompt = StrategyEngine.construct_adaptive_prompt(sanitized_input, persona_key)
    
    try:
        client = ModelManager.get_client()
    except Exception:
        return "🚫 CRITICAL ERROR: Client Init Failed."

    for model_name in candidate_models:
        try:
            # logger.info(f"🧠 Trying Engine: {model_name}")
            
            response = client.models.generate_content(
                model=model_name,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            raw_text = response.text.strip()
            data = json.loads(raw_text)
            
            # SUCCESS: Update sticky session
            ModelManager.update_champion(model_name)
            return format_telegram_response(data, model_name, persona_key)

        except Exception as e:
            logger.warning(f"⚠️ Failure on {model_name}: {e}. Switching to next...")
            continue

    return "🚫 CRITICAL ERROR: All available models failed."

def format_telegram_response(data: dict, model_name: str, persona_key: str) -> str:
    analysis = data.get("analysis_summary", "N/A")
    options = data.get("options", [])
    header = "👨‍💻 **ARCHITECT MODE**" if persona_key == "dev" else "👑 **VISIONARY MODE**"
    
    output = f"{header}\n🧠 _{analysis}_\n\n"
    for i, opt in enumerate(options, 1):
        output += (
            f"🔹 **Option {i}: {opt.get('strategy_mode')}** (Score: {opt.get('score_prediction')})\n"
            f"🖼️ *Visual:* {opt.get('visual_cue')}\n"
            f"📋 `COPY:`\n{opt.get('tweet_content')}\n\n"
        )
    output += f"⚙️ *Engine: {model_name}*"
    return output