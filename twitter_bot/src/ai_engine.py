import google.generativeai as genai
from google.api_core import exceptions
import logging
import re
import json
from src.app_config import Config

logger = logging.getLogger(__name__)

# --- 1. X ALGORITHM INTELLIGENCE (SHARED KNOWLEDGE) ---
# Derived from 'home-mixer/scorers/weighted_scorer.rs'
X_ALGO_RULES = """
--- X ALGORITHM RULES (INTERNAL KNOWLEDGE) ---
Optimize for these WeightedScorer.rs variables:
1. REPLY_WEIGHT: Questions/Debates trigger high reply scores.
2. PROFILE_CLICK_WEIGHT: Curiosity gaps (e.g., "Check pinned") force profile visits.
3. PHOTO_EXPAND_WEIGHT: Vertical images/charts that require clicking.
4. DWELL_TIME: Long-form, high-value content keeps users reading.
5. VQV_WEIGHT (Video): Video content >2s gets a boost.
"""

# --- 2. DUAL PERSONA DEFINITIONS ---
PERSONAS = {
    "dev": {
        "role": "THE ARCHITECT (@pepetopia_dev)",
        "tone": "Technical, Transparent, 'Builder-to-Builder', Humble but Smart.",
        "goals": "Build trust through code. Solve problems publicly. NO SHILLING.",
        "style_guide": "Use technical jargon (Rust, RPC, Latency). Explain 'How'. Focus on Engineering Wins.",
        "example_hook": "Spent 4 hours debugging Solana RPC latency. Here is the fix:"
    },
    "brand": {
        "role": "THE VISIONARY (@pepetopia)",
        "tone": "High-Status, Intellectual, 'The Insider', Cult-Leader Vibes.",
        "goals": "Dominate the narrative. Sell the vision/freedom. Maximize Hype without being cheap.",
        "style_guide": "Focus on 'Why'. Talk about Privacy, Freedom, Ecosystem Dominance. Be bold/arrogant.",
        "example_hook": "Privacy is not a feature. It is the only way to survive the next cycle."
    }
}

class StrategyEngine:
    """
    Decides the engagement strategy based on the selected PERSONA and X Algorithm.
    """
    
    @staticmethod
    def construct_adaptive_prompt(user_input: str, persona_key: str) -> str:
        """
        Builds a context-aware prompt combining the Persona + Algorithm Rules.
        """
        persona = PERSONAS.get(persona_key, PERSONAS["brand"])  # Default to Brand
        
        return f"""
--- IDENTITY PROTOCOL: {persona['role']} ---
Tone: {persona['tone']}
Goal: {persona['goals']}
Style: {persona['style_guide']}

{X_ALGO_RULES}

--- INPUT CONTEXT ---
"{user_input}"

--- MISSION ---
Generate 3 HIGH-RANKING tweet options acting strictly as {persona['role']}.
Each option must target a specific X Algorithm metric.

--- STRATEGY MODES (Select 3 distinct ones) ---
1. MODE_TECHNICAL_DEEP_DIVE (Target: DWELL_TIME) -> Best for Dev
2. MODE_CONTROVERSIAL_TAKE (Target: REPLY_WEIGHT) -> Best for Brand
3. MODE_VISUAL_ALPHA (Target: PHOTO_EXPAND_WEIGHT) -> Best for Charts/Screenshots
4. MODE_ECOSYSTEM_BAIT (Target: PROFILE_CLICK_WEIGHT) -> Best for Teasers

--- OUTPUT FORMAT (STRICT JSON) ---
Output ONLY a valid JSON object. No markdown.
{{
  "analysis_summary": "Why this fits the {persona['role']} persona.",
  "options": [
    {{
      "strategy_mode": "MODE_NAME",
      "target_metric": "ALGO_VARIABLE",
      "score_prediction": 95,
      "visual_cue": "Specific description of image/video.",
      "tweet_content": "Tweet text here. End with #{'PepetopiaDev' if persona_key == 'dev' else 'Pepetopia'}."
    }}
  ]
}}
"""

class ModelManager:
    """
    Manages dynamic discovery, fallback logic, and 'Sticky' model selection.
    CRITICAL: Logic is preserved to ensure continuity of service across model limits.
    """
    _cached_models = []
    _current_index = 0

    @staticmethod
    def _extract_version(model_name: str) -> float:
        match = re.search(r'(\d+(?:\.\d+)?)', model_name)
        if match:
            return float(match.group(1))
        return 0.0

    @classmethod
    def get_prioritized_models(cls):
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
            
            # Sort: Version Descending -> Pro over Flash
            valid_models.sort(key=lambda x: (cls._extract_version(x), 'pro' in x), reverse=True)
            
            if not valid_models:
                logger.warning("⚠️ No models found dynamically. Using fallback.")
                valid_models = ["models/gemini-1.5-pro", "models/gemini-1.5-flash"]

            logger.info(f"✅ Model Priority List: {valid_models}")
            cls._cached_models = valid_models
            return valid_models

        except Exception as e:
            logger.error(f"❌ Model discovery failed: {e}")
            return ["models/gemini-1.5-flash"]

    @classmethod
    def update_champion(cls, model_name):
        if model_name in cls._cached_models:
            cls._current_index = cls._cached_models.index(model_name)

    @classmethod
    def get_rotated_list(cls):
        models = cls.get_prioritized_models()
        if not models:
            return []
        if cls._current_index >= len(models):
            cls._current_index = 0
        return models[cls._current_index:] + models[:cls._current_index]

def analyze_and_draft(user_input: str) -> str:
    """
    Orchestrates the AI interaction with Persona Routing.
    """
    # 1. PARSE PERSONA TAG (ROUTING LAYER)
    persona_key = "brand" # Default
    clean_input = user_input

    # Regex to find @pepetopia_dev or @pepetopia at the end
    match = re.search(r'(@pepetopia_dev|@pepetopia)\s*$', user_input, re.IGNORECASE)
    if match:
        tag = match.group(1).lower()
        if "dev" in tag:
            persona_key = "dev"
        else:
            persona_key = "brand"
        
        # Remove the tag from the input so AI doesn't repeat it
        clean_input = user_input[:match.start()].strip()

    # 2. SECURITY: Input Sanitization
    sanitized_input = re.sub(r'[^\w\s@#.,!?\-\'\"]', '', clean_input[:1500])
    
    # 3. GENERATE PROMPT
    candidate_models = ModelManager.get_rotated_list()
    final_prompt = StrategyEngine.construct_adaptive_prompt(sanitized_input, persona_key)

    # 4. EXECUTE AI CHAIN
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name, 
                system_instruction="You are a JSON-only generator. Output raw JSON without Markdown."
            )
            
            response = model.generate_content(final_prompt)
            raw_text = response.text.strip()
            
            # Cleaner
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```json|^```|```$", "", raw_text, flags=re.MULTILINE).strip()

            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                logger.error(f"❌ JSON Error on {model_name}. Raw: {raw_text[:50]}...")
                raise exceptions.GoogleAPICallError("Malformed JSON")

            # Success
            ModelManager.update_champion(model_name)
            return format_telegram_response(data, model_name, persona_key)

        except exceptions.ResourceExhausted:
            logger.warning(f"⚠️ Quota Exceeded for {model_name}. Switching...")
            continue   
        except Exception as e:
            logger.error(f"❌ Error with {model_name}: {e}. Switching...")
            continue

    return "🚫 CRITICAL ERROR: All AI models failed."

def format_telegram_response(data: dict, model_name: str, persona_key: str) -> str:
    """
    Formats the output with visual cues for the active persona.
    """
    analysis = data.get("analysis_summary", "No analysis.")
    options = data.get("options", [])
    
    # Header Icon based on Persona
    header_icon = "👨‍💻" if persona_key == "dev" else "👑"
    role_title = "BUILDER MODE" if persona_key == "dev" else "VISIONARY MODE"

    output = f"{header_icon} **{role_title} ACTIVE**\n"
    output += f"🧠 _Analysis: {analysis}_\n\n"
    
    for i, opt in enumerate(options, 1):
        mode = opt.get('strategy_mode', 'Unknown')
        score = opt.get('score_prediction', 0)
        visual = opt.get('visual_cue', '-')
        content = opt.get('tweet_content', '')
        
        output += (
            f"🔹 **Option {i}: {mode}** (Score: {score})\n"
            f"🖼️ *Visual:* {visual}\n"
            f"📋 `COPY:`\n{content}\n\n"
        )
        
    output += f"⚙️ *Engine: {model_name.replace('models/', '')}*"
    return output