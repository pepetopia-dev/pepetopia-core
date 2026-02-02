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
1. REPLY_WEIGHT: High signal questions.
2. PROFILE_CLICK_WEIGHT: Curiosity gaps.
3. PHOTO_EXPAND_WEIGHT: Refer to visuals.
4. DWELL_TIME: High-density info.
5. VQV_WEIGHT: Video context.
"""

# --- 2. PERSONA DEFINITIONS ---
PERSONAS = {
    "dev": {
        "role": "THE ARCHITECT (@pepetopia_dev)",
        "tone": "Technical, Builder-to-Builder, Analytical.",
        "drift_guard": "STAY ON TOPIC. No random language pivots."
    },
    "brand": {
        "role": "THE VISIONARY (@pepetopia)",
        "tone": "High-Status, Intellectual, Commanding.",
        "drift_guard": "STAY ON TOPIC. Connect to ecosystem vision."
    }
}

class StrategyEngine:
    @staticmethod
    def construct_adaptive_prompt(user_input: str, persona_key: str) -> str:
        persona = PERSONAS.get(persona_key, PERSONAS["brand"])
        return f"""
--- IDENTITY: {persona['role']} ---
Tone: {persona['tone']} | Constraint: {persona['drift_guard']}

{X_ALGO_RULES}

--- INPUT ---
"{user_input}"

--- MISSION ---
Generate 3 tweet options strictly following the input topic.
Output raw JSON only.

{{
  "analysis_summary": "...",
  "options": [
    {{
      "strategy_mode": "...",
      "target_metric": "...",
      "score_prediction": 95,
      "visual_cue": "...",
      "tweet_content": "..."
    }}
  ]
}}
"""

class ModelManager:
    """
    Handles dynamic discovery with STABILITY filtering.
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
    def _model_ranking(model_name: str):
        # Prefer stable 2.0 and 1.5 models over experimental ones
        version = float(re.search(r'(\d+(?:\.\d+)?)', model_name).group(1)) if re.search(r'(\d+(?:\.\d+)?)', model_name) else 0.0
        
        score = version * 10
        if "pro" in model_name: score += 2
        if "flash" in model_name: score += 1
        if "exp" in model_name or "preview" in model_name: score -= 5 # Deprioritize experimental
        
        return score

    @classmethod
    def get_rotated_list(cls):
        if not cls._cached_models:
            try:
                client = cls.get_client()
                logger.info("📡 Discovering stable models...")
                
                all_api_models = [m.name.replace('models/', '') for m in client.models.list()]
                
                # Filter for usable Gemini models only
                usable = [m for m in all_api_models if 'gemini' in m and 'embedding' not in m and 'aqa' not in m]
                
                # Rank by version and stability
                usable.sort(key=cls._model_ranking, reverse=True)
                
                cls._cached_models = usable
                logger.info(f"✅ Filtered Model Chain: {cls._cached_models}")
            except Exception as e:
                logger.error(f"❌ Discovery failed: {e}")
                return ["gemini-2.0-flash", "gemini-1.5-flash"]

        return cls._cached_models[cls._current_index:] + cls._cached_models[:cls._current_index]

    @classmethod
    def update_champion(cls, model_name):
        if model_name in cls._cached_models:
            cls._current_index = cls._cached_models.index(model_name)

def escape_markdown(text: str) -> str:
    """
    Escapes reserved MarkdownV2 characters to prevent Telegram parse errors.
    """
    # Specifically target characters that break style tags and headers
    reserved_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(reserved_chars), r'\\\1', text)

def analyze_and_draft(user_input: str) -> str:
    persona_key = "brand"
    clean_input = user_input
    match = re.search(r'(@pepetopia_dev|@pepetopia)\s*$', user_input, re.IGNORECASE)
    if match:
        tag = match.group(1).lower()
        persona_key = "dev" if "dev" in tag else "brand"
        clean_input = user_input[:match.start()].strip()

    enriched_input = extract_url_content(clean_input)
    candidate_models = ModelManager.get_rotated_list()
    final_prompt = StrategyEngine.construct_adaptive_prompt(enriched_input[:2000], persona_key)
    client = ModelManager.get_client()

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=final_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text.strip())
            ModelManager.update_champion(model_name)
            return format_telegram_response(data, model_name, persona_key)

        except Exception as e:
            logger.warning(f"⚠️ {model_name} failed: {e}. Switching...")
            continue

    return "🚫 All models exhausted."

def format_telegram_response(data: dict, model_name: str, persona_key: str) -> str:
    # Use HTML or Markdown escaping to prevent 400 Bad Request
    header = "👨‍💻 ARCHITECT MODE" if persona_key == "dev" else "👑 VISIONARY MODE"
    analysis = data.get("analysis_summary", "N/A")
    
    # Building response as a list of lines for cleaner handling
    res = [f"*{header}*", f"_{analysis}_", ""]
    
    for i, opt in enumerate(data.get("options", []), 1):
        content = opt.get('tweet_content', '')
        res.append(f"🔹 *Option {i}: {opt.get('strategy_mode')}*")
        res.append(f"🖼️ Visual: {opt.get('visual_cue')}")
        res.append(f"📋 ` {content} `\n")
    
    res.append(f"⚙️ Engine: {model_name}")
    
    # Final join and escape check
    final_text = "\n".join(res)
    return final_text