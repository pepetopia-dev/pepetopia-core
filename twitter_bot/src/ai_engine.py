import google.generativeai as genai
from google.api_core import exceptions
import re
from src.app_config import Config
from src.utils import logger

# Global Cache
CACHED_MODEL_LIST = []

# --- TWITTER ALGORITHM OPTIMIZED PROMPT ---
# Based on Open Source insights (Heavy Ranker & Toxicity Model)
SYSTEM_PROMPT = """
You are a Crypto Twitter Expert representing 'Pepetopia' ($PEPETOPIA).
Your Goal: Write high-ranking replies based on Twitter's open-source algorithm.

CTX (Context) AWARENESS:
- If target is a DEV/FOUNDER (e.g., Vitalik, Toly): Be technical, analytical, respectful.
- If target is NEWS (e.g., WatcherGuru): Be fast, summarize, or add a witty take.
- If target is DEGEN/INFLUENCER (e.g., Ansem): Be informal, use slang (WAGMI, bullish), match the vibe.

ALGORITHM OPTIMIZATION RULES (CRITICAL):
1. RELEVANCE IS KING: Your reply MUST strictly relate to the tweet's topic. (Cosine similarity).
2. ASK QUESTIONS: Questions drive replies. Replies drive ranking.
3. ZERO TOXICITY: No insults, no aggression. (Avoids shadowban).
4. LENGTH: Short is better. Ideal: 100-180 characters. Max: 280.
5. NO OUTBOUND LINKS: Links reduce visibility. Never use them.

Output format: Just the text of the reply. No quotes.
"""

def _extract_version(model_name: str) -> float:
    match = re.search(r'(\d+\.\d+)', model_name)
    if match:
        return float(match.group(1))
    return 1.0

def _get_dynamic_model_list():
    global CACHED_MODEL_LIST
    if CACHED_MODEL_LIST:
        return CACHED_MODEL_LIST

    genai.configure(api_key=Config.GEMINI_API_KEY)
    
    try:
        logger.info("📡 Fetching dynamic AI model list...")
        all_models = genai.list_models()
        valid_models = []
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                valid_models.append(m.name)
        
        valid_models.sort(key=_extract_version, reverse=True)
        
        if not valid_models:
            raise ValueError("No valid models found.")

        CACHED_MODEL_LIST = valid_models
        return valid_models

    except Exception as e:
        logger.error(f"⚠️ Dynamic fetch failed: {e}. Using fallback.")
        return ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]

def generate_reply(tweet_content: str, author: str) -> str:
    """
    Generates an algorithm-optimized reply.
    """
    priority_models = _get_dynamic_model_list()

    # We inject the author name into the prompt so the AI can "guess" the context
    user_prompt = f"""
    Target Account: @{author}
    Tweet Content: "{tweet_content}"
    
    Task: Write a context-aware, algorithm-friendly reply.
    """

    for model_name in priority_models:
        try:
            model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
            response = model.generate_content(user_prompt)
            clean_reply = response.text.strip()
            
            if len(clean_reply) > 280:
                return clean_reply[:277] + "..."
            
            logger.info(f"✅ Generated with {model_name}")
            return clean_reply

        except Exception as e:
            logger.warning(f"⚠️ Error with {model_name}: {e}")
            continue

    return "Error: AI Brain Unavailable."