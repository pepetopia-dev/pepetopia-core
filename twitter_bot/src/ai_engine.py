from google import genai
from google.genai import types
import logging
import re
import json
from src.app_config import Config
from src.utils import extract_url_content

logger = logging.getLogger(__name__)

# --- 1. X ALGORITHM RULES (IMMUTABLE CORE) ---
X_ALGO_RULES = """
--- X ALGORITHM OPTIMIZATION RULES ---
Your output MUST maximize these internal scoring variables:
1. REPLY_WEIGHT: Provoke debates or ask high-signal questions.
2. PROFILE_CLICK_WEIGHT: Create "Curiosity Gaps" (e.g., "See pinned tweet for the full chart").
3. PHOTO_EXPAND_WEIGHT: Reference visual data (Charts, Screenshots) that forces a click.
4. DWELL_TIME: Use high-value, dense information to keep users reading >15s.
5. VQV_WEIGHT: Mention video/animation context if applicable.
"""

# --- 2. REFINED PERSONA DEFINITIONS ---
PERSONAS = {
    "dev": {
        "role": "THE ARCHITECT (@pepetopia_dev)",
        "tone": "Solution-Oriented, Transparent, 'Builder-to-Builder', Analytical.",
        "goals": "Build trust through technical competence. Explain mechanics, not just tools. NO SHILLING.",
        "style_guide": "Focus on architecture, latency, security, and logic. Do not mention specific languages unless asked.",
        "drift_guard": "STAY ON TOPIC. Do not pivot to random tech stacks."
    },
    "brand": {
        "role": "THE VISIONARY (@pepetopia)",
        "tone": "High-Status, Intellectual, 'The Insider', Commanding.",
        "goals": "Dominate the narrative. Frame Pepetopia as the inevitable future. Maximize Hype intelligently.",
        "style_guide": "Focus on 'Why' and 'Macro Impact'. Talk about Freedom, Privacy, and Dominance.",
        "drift_guard": "STAY ON TOPIC. Connect the input topic to the ecosystem vision."
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
CRITICAL: You must stick to the subject matter of the INPUT CONTEXT.

--- STRATEGY MODES (Choose 3 distinct ones) ---
1. MODE_TECHNICAL_DEEP_DIVE (Target: DWELL_TIME)
2. MODE_CONTROVERSIAL_TAKE (Target: REPLY_WEIGHT)
3. MODE_VISUAL_ALPHA (Target: PHOTO_EXPAND_WEIGHT)
4. MODE_ECOSYSTEM_BAIT (Target: PROFILE_CLICK_WEIGHT)

--- OUTPUT FORMAT (JSON ONLY) ---
Output purely valid JSON. No markdown formatting.
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
    Handles model selection using the NEW google-genai SDK.
    """
    _client = None
    _cached_models = []
    _current_index = 0

    @classmethod
    def get_client(cls):
        if not cls._client:
            cls._client = genai.Client(api_key=Config.GEMINI_API_KEY)
        return cls._client

    @classmethod
    def get_rotated_list(cls):
        if not cls._cached_models:
            try:
                client = cls.get_client()
                logger.info("📡 Discovering Gemini models via new SDK...")
                # List models and filter for Gemini generation models
                all_models = [
                    m.name for m in client.models.list() 
                    if 'gemini' in m.name and 'generateContent' in (m.supported_generation_methods or [])
                ]
                # Sort: Newest first (Basic string sort works well for gemini-2.0 vs 1.5)
                all_models.sort(reverse=True)
                
                cls._cached_models = all_models if all_models else ["gemini-2.0-flash", "gemini-1.5-pro"]
                logger.info(f"✅ Active Models: {cls._cached_models}")
            except Exception as e:
                logger.error(f"❌ Model discovery failed: {e}")
                return ["gemini-1.5-flash"]

        if cls._current_index >= len(cls._cached_models):
            cls._current_index = 0
        return cls._cached_models[cls._current_index:] + cls._cached_models[:cls._current_index]

    @classmethod
    def update_champion(cls, model_name):
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

    # 3. GENERATION (NEW SDK)
    candidate_models = ModelManager.get_rotated_list()
    final_prompt = StrategyEngine.construct_adaptive_prompt(sanitized_input, persona_key)
    client = ModelManager.get_client()

    for model_name in candidate_models:
        try:
            # Clean model name if it has 'models/' prefix (Old SDK legacy)
            clean_model_name = model_name.replace("models/", "")
            
            response = client.models.generate_content(
                model=clean_model_name,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"  # Native JSON enforcement!
                )
            )
            
            # Parsing
            raw_text = response.text.strip()
            data = json.loads(raw_text)
            
            ModelManager.update_champion(model_name)
            return format_telegram_response(data, clean_model_name, persona_key)

        except Exception as e:
            logger.error(f"❌ Failure on {model_name}: {e}")
            continue

    return "🚫 CRITICAL ERROR: All AI models failed."

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