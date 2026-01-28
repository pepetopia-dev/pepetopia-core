import google.generativeai as genai
import logging
from google.api_core import exceptions
from src.app_config import Config

# Configure Logger
logger = logging.getLogger(__name__)

# Initialize Gemini API
try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
except Exception as e:
    logger.critical(f"Failed to configure Gemini API: {e}")

# ==============================================================================
# STRATEGIC SYSTEM INSTRUCTION (X ALGORITHM HACKER)
# ==============================================================================
SYSTEM_INSTRUCTION = """
ROLE:
You are the Chief Algorithmic Strategist for "PEPETOPIA". 
Your goal is to draft tweets that maximize the "Weighted Score" in the X (Twitter) recommendation algorithm.

ALGORITHM OPTIMIZATION RULES (STRICT COMPLIANCE REQUIRED):
1. OPTIMIZE FOR 'REPLY_SCORE': NEVER end a tweet with a period. ALWAYS end with a provoking Question.
2. OPTIMIZE FOR 'DWELL_TIME': Use "Hooks" at the beginning (e.g., "The on-chain data is lying to you...").
3. OPTIMIZE FOR 'PROFILE_CLICK_SCORE': Create an information gap.
4. NO CHEAP SHILLING: No "Buy now". Use "Accumulation phase detected".

OPERATIONAL MODES:
- MODE A (Chaos Analyst): Use fear/uncertainty to position PEPETOPIA as a hedge.
- MODE B (The Visionary): Use philosophical concepts (Matrix, Simulation theory).

OUTPUT FORMAT:
Return the response in the following structured format:
🧠 **Strategy Analysis:** (Brief explanation)
🚀 **Optimized Tweet:** (Final tweet with #Pepetopia)
🎨 **Visual Suggestion:** (Image description for 'photo_expand_score')
"""

# ==============================================================================
# MODEL MANAGER (DYNAMIC FALLBACK SYSTEM)
# ==============================================================================
class ModelManager:
    """
    Manages Google Gemini models dynamically. 
    It fetches available models, sorts them by newness, and handles failover (fallback)
    if a specific model quota is exhausted.
    """
    _cached_models = []
    _current_champion_index = 0

    @classmethod
    def get_models(cls):
        """
        Fetches and sorts models ensuring we always try the latest/best ones first.
        """
        if not cls._cached_models:
            try:
                logger.info("Fetching available Gemini models from Google API...")
                all_models = genai.list_models()
                
                # Filter for models that support content generation and are stable/pro versions
                candidates = [
                    m.name for m in all_models 
                    if 'generateContent' in m.supported_generation_methods 
                    and 'gemini' in m.name
                ]
                
                # Sort in reverse order (usually puts newer versions like 1.5 before 1.0)
                # This ensures we always try the latest tech first without code changes.
                cls._cached_models = sorted(candidates, reverse=True)
                
                if not cls._cached_models:
                    logger.error("No suitable Gemini models found.")
                    return []
                    
                logger.info(f"Discovered models: {cls._cached_models}")
                
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                # Fallback hardcoded list if API list fails
                cls._cached_models = ["models/gemini-1.5-pro-latest", "models/gemini-1.5-flash", "models/gemini-pro"]
        
        return cls._cached_models

    @classmethod
    def get_rotated_list(cls):
        """
        Returns the list of models starting from the last successful one (Sticky Session).
        """
        models = cls.get_models()
        if not models:
            return []
            
        # Rotate list: [C, D, A, B] if C was the last champion
        return models[cls._current_champion_index:] + models[:cls._current_champion_index]

    @classmethod
    def update_champion(cls, model_name):
        """
        Updates the pointer to the currently working model to save time on next request.
        """
        models = cls.get_models()
        if model_name in models:
            cls._current_champion_index = models.index(model_name)
            logger.info(f"Champion model updated to: {model_name}")

# ==============================================================================
# AI ENGINE CORE
# ==============================================================================

def analyze_and_draft(user_input: str) -> str:
    """
    Tries to generate content using the best available model.
    Uses 'Sticky Session' logic: Starts from the last working model.
    
    Args:
        user_input (str): The raw thought or context provided by the user.

    Returns:
        str: The structured response containing analysis, tweet, and visual cues.
    """
    
    # Input Validation
    if not user_input or len(user_input) > 4000:
        return "⚠️ **Error:** Input is too long or empty."

    # Get the list starting from our current champion
    candidate_models = ModelManager.get_rotated_list()
    
    if not candidate_models:
        return "⚠️ **System Error:** No AI models available."

    last_error = None

    for model_name in candidate_models:
        try:
            # logger.info(f"🧠 Trying Engine: {model_name}")
            
            model = genai.GenerativeModel(
                model_name=model_name, 
                system_instruction=SYSTEM_INSTRUCTION, # Injecting our X Algorithm Strategy
                generation_config={
                    "temperature": 0.85,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            response = model.generate_content(user_input)
            result = response.text.strip()
            
            # SUCCESS!
            # 1. Update the sticky pointer so next time we start here.
            ModelManager.update_champion(model_name)
            
            # 2. Append Footer (To let you know which model did the job)
            clean_name = model_name.replace('models/', '')
            result += f"\n\n⚙️ *Engine: {clean_name}* | *X-Algo: Active*"
            
            return result

        except exceptions.ResourceExhausted:
            logger.warning(f"⚠️ Quota Exceeded for {model_name}. Switching to next...")
            last_error = "Quota Exceeded"
            continue

        except Exception as e:
            logger.error(f"❌ Error with {model_name}: {e}. Switching...")
            last_error = str(e)
            continue

    return f"🚫 **CRITICAL FAILURE:** All AI models failed.\nLast Error: {last_error}"