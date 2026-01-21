import google.generativeai as genai
from src.app_config import Config
from src.utils import logger

# System Prompt defines the persona and constraints
SYSTEM_PROMPT = """
You are a Crypto Twitter Expert representing 'Pepetopia' ($PEPETOPIA).
Goal: Write SHORT, ENGAGING replies to crypto tweets.

CONSTRAINTS:
1. Max 280 Characters (Hard limit).
2. Language: English (Casual, crypto-native).
3. Tone: Witty, analytical, or supportive. Not robotic.
4. No hashtags unless strictly necessary.

Do not be sycophantic. Provide value or entertainment.
"""

def generate_reply(tweet_content: str, author: str) -> str:
    """
    Generates a reply using Google Gemini Flash model.
    """
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            'gemini-1.5-flash', 
            system_instruction=SYSTEM_PROMPT
        )
        
        user_prompt = f"""
        Tweet Author: @{author}
        Tweet Content: "{tweet_content}"
        
        Task: Write a reply under 280 characters.
        """
        
        response = model.generate_content(user_prompt)
        clean_reply = response.text.strip()
        
        # Double check length safety
        if len(clean_reply) > 280:
            logger.warning("AI generated content too long. Truncating.")
            return clean_reply[:277] + "..."
            
        return clean_reply

    except Exception as e:
        logger.error(f"AI Generation Error: {e}")
        return "Error generating reply."