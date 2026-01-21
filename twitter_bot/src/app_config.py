import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Central configuration management.
    """
    
    # Security: Fail immediately if keys are missing
    try:
        GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
        TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
        TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
    except KeyError as e:
        print(f"CRITICAL ERROR: Missing environment variable {e}")
        sys.exit(1)

    # Operational Constraints
    TIMEZONE = "Europe/Istanbul"
    WORK_START_HOUR = 8 
    WORK_END_HOUR = 1   
    
    DEV_MODE = True
    # Nitter Instances (Failover list)
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.poast.org",
        "https://nitter.privacy.com.de"
    ]

    # TARGET ACCOUNTS STRATEGY (The 3-Layer Method)
    TARGET_ACCOUNTS = [
        # 1. Tech Leaders (Technical Tone)
        "solana",
        "aeyakovenko",
        "rajgokal",
        "VitalikButerin",

        # 2. News Aggregators (Witty/Summary Tone)
        "WatcherGuru",
        "WhaleWire",
        "DeItaone",

        # 3. Influencers/Degens (Informal/Cultural Tone)
        "Ansem",
        "MustStopMurad",
        "blknoiz06",
        "trader1sz",
        "ElonMusk"
    ]