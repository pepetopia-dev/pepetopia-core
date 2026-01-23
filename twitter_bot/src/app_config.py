import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Central configuration management for the Strategic Advisor Bot.
    """
    
    # Security: Fail immediately if critical keys are missing
    try:
        GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
        TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
        TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
    except KeyError as e:
        print(f"CRITICAL ERROR: Missing environment variable {e}")
        sys.exit(1)

    # AI Model Configuration
    # Using Flash for speed, but Pro is recommended for complex reasoning if needed.
    AI_MODEL_NAME = "gemini-1.5-flash"