import logging
import re
import json
import time
from typing import List, Dict, Optional
from google import genai
from google.genai import types
from src.app_config import Config
from src.utils import extract_url_content

# Configure module-level logger
logger = logging.getLogger(__name__)

# --- CONSTANTS & ALGORITHM WEIGHTS ---
X_ALGO_WEIGHTS = """
OBJECTIVE: MAXIMIZE TWEET SCORING BASED ON THESE X ALGORITHM WEIGHTS:
1. REPLY_WEIGHT (High): Discussion starters, controversial takes, questions.
2. RETWEET_WEIGHT (Medium): High-value utility, breaking news, relatable memes.
3. DWELL_TIME_WEIGHT (High): Dense technical threads, long-form content, "read more" hooks.
4. PHOTO_EXPAND_WEIGHT (Medium): Visual cues, referring to attached images/diagrams.
5. PROFILE_CLICK_WEIGHT (Low): Curiosity gaps that lead to profile investigation.
"""

class PersonaManager:
    """
    Manages the tone and stylistic constraints for different bot personas.
    """
    PERSONAS = {
        "dev": {
            "role": "SENIOR SOFTWARE ARCHITECT (@pepetopia_dev)",
            "style": "Technical, terse, authoritative, code-centric. Uses jargon correctly.",
            "directive": "Focus on implementation details, performance metrics, and architectural implications. optimize for DWELL_TIME (Technical depth)."
        },
        "brand": {
            "role": "ECOSYSTEM VISIONARY (@pepetopia)",
            "style": "Inspiring, high-status, community-focused, forward-looking.",
            "directive": "Focus on the big picture, market impact, and community growth. Optimize for RETWEET_WEIGHT and REPLY_WEIGHT (Virality)."
        }
    }

    @staticmethod
    def get_persona(input_text: str) -> tuple[str, dict]:
        if "@pepetopia_dev" in input_text.lower():
            return "dev", PersonaManager.PERSONAS["dev"]
        return "brand", PersonaManager.PERSONAS["brand"]

class ModelChain:
    """
    Implements DYNAMIC discovery and rotation mechanism for Gemini Models.
    Fetches real-time model list from Google API, sorts by version/capability.
    """
    _client: Optional[genai.Client] = None
    _cached_models: List[str] = []
    _last_fetch_time: float = 0
    _CACHE_DURATION = 3600  # Refresh model list every 1 hour

    @classmethod
    def _initialize_client(cls):
        if not cls._client:
            cls._client = genai.Client(api_key=Config.GEMINI_API_KEY)

    @staticmethod
    def _calculate_model_score(model_name: str) -> float:
        """
        Scoring algorithm to rank models based on freshness and capability.
        Higher score = Higher priority in the chain.
        """
        score = 0.0
        
        # 1. Extract Version (e.g., 2.0, 1.5, 1.0)
        version_match = re.search(r'gemini-(\d+\.?\d*)', model_name)
        if version_match:
            score += float(version_match.group(1)) * 100  # Major weight on version

        # 2. Capability Hierarchy
        if "pro" in model_name:
            score += 10  # Prefer Pro for reasoning
        elif "flash" in model_name:
            score += 5   # Prefer Flash for speed/cost if Pro matches
        elif "ultra" in model_name:
            score += 20  # Ultra is top tier if available
            
        # 3. Recency / Experimental Preference
        # If user wants the absolute latest, experimental models often have newer features.
        if "exp" in model_name or "preview" in model_name:
            score += 1   # Slight boost to break ties with stable versions if versions are equal
            
        # 4. Demote Embedding/Vision-only models (Safety filter)
        if "vision" in model_name and "pro" not in model_name: # Simple filter, logic can be refined
            score -= 500
            
        return score

    @classmethod
    def _fetch_and_rank_models(cls) -> List[str]:
        """
        Queries Google API for ALL available models and sorts them.
        """
        cls._initialize_client()
        try:
            logger.info("📡 Contacting Google API for latest model list...")
            all_models_raw = list(cls._client.models.list())
            
            # Filter only generative Gemini models (exclude embedding, aqa, etc.)
            # The API returns objects, we need the 'name' attribute which usually looks like 'models/gemini-1.5-pro'
            gemini_models = [
                m.name.replace('models/', '') 
                for m in all_models_raw 
                if 'gemini' in m.name and 'embedding' not in m.name
            ]
            
            if not gemini_models:
                logger.warning("⚠️ No models found via API. Using fallback list.")
                return ["gemini-1.5-pro", "gemini-1.5-flash"]

            # Sort based on our scoring algorithm (Highest score first)
            sorted_models = sorted(gemini_models, key=cls._calculate_model_score, reverse=True)
            
            logger.info(f"✅ Discovered & Ranked Models: {sorted_models}")
            return sorted_models

        except Exception as e:
            logger.error(f"❌ Model discovery failed: {e}")
            # Fallback if API list fails
            return ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]

    @classmethod
    def get_models(cls) -> List[str]:
        current_time = time.time()
        # Refresh cache if empty or expired
        if not cls._cached_models or (current_time - cls._last_fetch_time > cls._CACHE_DURATION):
            cls._cached_models = cls._fetch_and_rank_models()
            cls._last_fetch_time = current_time
        return cls._cached_models

    @classmethod
    def get_client(cls):
        cls._initialize_client()
        return cls._client

class StrategyEngine:
    @staticmethod
    def construct_system_prompt(persona: dict) -> str:
        return f"""
You are {persona['role']}.
Style: {persona['style']}
Mission: {persona['directive']}

{X_ALGO_WEIGHTS}

CRITICAL RULES:
1. DO NOT ALWAYS ASK QUESTIONS. Analyze the input. If it's technical, provide a solution (Dwell Time). If it's news, state an opinion (Retweet).
2. NO GENERIC AI SLOP. No "Here is a tweet", "Buckle up", "Let's dive in". Just the content.
3. OUTPUT FORMAT: strict JSON only.
"""

    @staticmethod
    def construct_user_prompt(context_text: str) -> str:
        return f"""
INPUT CONTEXT:
"{context_text[:3000]}"

TASK:
Generate 3 distinct tweet options based on the input.
1. Option 1: Optimize for REPLY_WEIGHT (Question/Debate).
2. Option 2: Optimize for DWELL_TIME (Deep dive/Technical insight/Thread-hook).
3. Option 3: Optimize for RETWEET_WEIGHT (High signal/News/Meme-able).

JSON OUTPUT STRUCTURE:
{{
  "analysis": "Brief reasoning of input topic.",
  "options": [
    {{
      "type": "High Reply",
      "content": "..."
    }},
    {{
      "type": "High Dwell Time",
      "content": "..."
    }},
    {{
      "type": "High Retweet",
      "content": "..."
    }}
  ]
}}
"""

def analyze_and_draft(user_input: str) -> str:
    """
    Main orchestrator function.
    """
    persona_key, persona_data = PersonaManager.get_persona(user_input)
    
    clean_input = re.sub(r'@pepetopia(_dev)?', '', user_input, flags=re.IGNORECASE).strip()
    enriched_context = extract_url_content(clean_input) or clean_input

    # Get dynamically fetched models
    models = ModelChain.get_models()
    client = ModelChain.get_client()
    
    system_instruction = StrategyEngine.construct_system_prompt(persona_data)
    prompt = StrategyEngine.construct_user_prompt(enriched_context)

    for model_name in models:
        try:
            logger.info(f"⚡ Attempting generation with: {model_name} [{persona_key.upper()}]")
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.7 
                )
            )
            
            result_json = json.loads(response.text)
            return format_response(result_json, model_name, persona_key)

        except Exception as e:
            logger.warning(f"⚠️ Model {model_name} failed/exhausted. Error: {e}")
            logger.info("🔄 Switching to next available model in chain...")
            continue 
            
    return "🚫 SYSTEM FAILURE: All AI models are currently unavailable. Please try again later."

def format_response(data: dict, model_name: str, persona_key: str) -> str:
    header_icon = "👨‍💻" if persona_key == "dev" else "🔮"
    header_title = "ARCHITECT OUTPUT" if persona_key == "dev" else "VISIONARY OUTPUT"
    
    output = [f"{header_icon} *{header_title}*"]
    output.append(f"_{data.get('analysis', 'Analysis complete.')}_")
    output.append("")
    
    options = data.get("options", [])
    for i, opt in enumerate(options, 1):
        strategy = opt.get('type', 'General')
        content = opt.get('content', '')
        output.append(f"*{i}. Strategy: {strategy}*")
        output.append(f"`{content}`")
        output.append("")

    output.append(f"⚙️ _Engine: {model_name}_")
    return "\n".join(output)