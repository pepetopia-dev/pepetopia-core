import google.generativeai as genai
from google.api_core import exceptions
import logging
import re
import json
from src.app_config import Config

logger = logging.getLogger(__name__)

# --- STRATEGIC CONTEXT ---
# PEPETOPIA IDENTITY & ALGORITHM MAPPING
# Mapped directly from 'home-mixer/scorers/weighted_scorer.rs'
PROJECT_CONTEXT = """
Project: PEPETOPIA
Ticker: PEPETOPIA
Identity: A sophisticated crypto ecosystem.
Tone: Intellectual, High-Signal, 'The Insider', slightly arrogant but valid.

--- X ALGORITHM WEIGHTS (INTERNAL KNOWLEDGE) ---
The following weights determine tweet visibility. Use them to craft the strategy:
1. REPLY_WEIGHT: High priority. Questions trigger replies.
2. PROFILE_CLICK_WEIGHT: Curiosity gaps that force users to visit the profile.
3. PHOTO_EXPAND_WEIGHT: Images that require clicking to see full details (e.g., tall infographics).
4. VQV_WEIGHT (Video Quality View): Video content > 2 seconds is boosted.
5. DWELL_TIME: Long-form text that hooks the reader increases score.
6. NEGATIVE SIGNALS (AVOID): Blocks, Mutes, Reports drastically reduce visibility.
"""

class StrategyEngine:
    """
    Decides the engagement strategy based on X's Open Source Algorithm parameters.
    It acts as a 'Pre-Processing Layer' before generating the actual content.
    """
    
    @staticmethod
    def construct_adaptive_prompt(user_input: str) -> str:
        """
        Constructs a prompt that forces Gemini to act as the 'WeightedScorer' from the X Algorithm.
        It generates options maximizing specific variables found in 'weighted_scorer.rs'.
        """
        return f"""
{PROJECT_CONTEXT}

--- INPUT TWEET ---
"{user_input}"

--- MISSION ---
Analyze the input tweet. Then, generate 3 DISTINCT reply options. 
Each option MUST target a specific variable from the X Algorithm Source Code.

--- STRATEGY MODES (Select 3 distinct ones) ---
1. MODE_REPLY_FARM (Targets: REPLY_WEIGHT):
   - End with a controversial question or a "Call to Action".
   - Goal: Maximize comment section density.
   
2. MODE_PROFILE_BAIT (Targets: PROFILE_CLICK_WEIGHT):
   - Tease "Alpha" or hidden info.
   - Example phrase: "The full chart is in my pinned tweet..."
   - Goal: Force a profile visit.

3. MODE_VISUAL_HOOK (Targets: PHOTO_EXPAND_WEIGHT / VQV_WEIGHT):
   - Suggest a specific visual (Meme or Chart).
   - Text must reference the image to force an expand.
   - Goal: Stop the scroll.

4. MODE_DWELL_MAX (Targets: DWELL_TIME):
   - Longer, insightful text.
   - Use "Step-by-step" analysis format.
   - Goal: Keep user reading for >15 seconds.

--- OUTPUT FORMAT (STRICT JSON) ---
Output ONLY a valid JSON object. No markdown.
{{
  "analysis_summary": "Brief logic on why these strategies fit the input.",
  "options": [
    {{
      "strategy_mode": "MODE_NAME",
      "target_metric": "e.g., PROFILE_CLICK_WEIGHT",
      "score_prediction": 95,
      "visual_cue": "Description of image/video to attach. Be specific.",
      "tweet_content": "The tweet text here. No hashtags in sentences. End with #Pepetopia."
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
            
            # Sort by version descending (e.g., 2.0 > 1.5)
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
    Main orchestration function.
    1. Sanitizes input.
    2. Uses 'Sticky Session' to get the best model.
    3. Generates algorithm-compliant strategies.
    4. Formats for Telegram.
    """
    candidate_models = ModelManager.get_rotated_list()
    
    # SECURITY: Input Sanitization to prevent prompt injection or token overflow
    sanitized_input = re.sub(r'[^\w\s@#.,!?\-\'\"]', '', user_input[:1200])
    
    final_prompt = StrategyEngine.construct_adaptive_prompt(sanitized_input)

    for model_name in candidate_models:
        try:
            # logger.info(f"🧠 Trying Engine: {model_name}")
            
            # Using strict system instructions for JSON reliability
            model = genai.GenerativeModel(
                model_name, 
                system_instruction="You are a JSON-only generator. Output raw JSON without Markdown formatting."
            )
            
            response = model.generate_content(final_prompt)
            raw_text = response.text.strip()
            
            # Parser: Remove markdown code blocks if AI adds them (Common LLM behavior)
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```json|^```|```$", "", raw_text, flags=re.MULTILINE).strip()

            # Validation: Ensure strict JSON
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                logger.error(f"❌ JSON Decode Error on {model_name}. Raw: {raw_text[:50]}...")
                # Treat malformed JSON as a model failure to trigger fallback
                raise exceptions.GoogleAPICallError("Malformed JSON response")

            # SUCCESS PATH
            # 1. Update Sticky Session
            ModelManager.update_champion(model_name)
            
            # 2. Format & Return
            return format_telegram_response(data, model_name)

        except exceptions.ResourceExhausted:
            logger.warning(f"⚠️ Quota Exceeded for {model_name}. Switching...")
            continue
            
        except Exception as e:
            logger.error(f"❌ Error with {model_name}: {e}. Switching...")
            continue

    return "🚫 CRITICAL ERROR: All AI models failed. Please check logs."

def format_telegram_response(data: dict, model_name: str) -> str:
    """
    Formats the JSON data into a readable Telegram HTML/Markdown message.
    """
    analysis = data.get("analysis_summary", "No analysis provided.")
    options = data.get("options", [])
    
    output = f"🧠 **X-Algo Strategy Analysis:**\n_{analysis}_\n\n"
    
    for i, opt in enumerate(options, 1):
        mode = opt.get('strategy_mode', 'Unknown Mode')
        metric = opt.get('target_metric', 'Unknown Metric')
        score = opt.get('score_prediction', 0)
        visual = opt.get('visual_cue', 'No media suggested')
        content = opt.get('tweet_content', '')
        
        output += (
            f"🔹 **Option {i}: {mode}**\n"
            f"🎯 *Target:* `{metric}` (Est. Score: {score})\n"
            f"🖼️ *Visual:* {visual}\n"
            f"📋 `COPY BELOW:`\n"
            f"{content}\n\n"
        )
        
    output += f"⚙️ *Engine: {model_name.replace('models/', '')}*"
    return output