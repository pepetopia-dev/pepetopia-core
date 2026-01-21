import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Central configuration management.
    Validates that all necessary environment variables are present on startup.
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
    WORK_START_HOUR = 8  # 08:00 AM
    WORK_END_HOUR = 1    # 01:00 AM (Next Day)
    
    # Nitter Instances (Failover list)
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.poast.org",
        "https://nitter.privacy.com.de"
    ]

    # Target Accounts
    TARGET_ACCOUNTS = [
        "VitalikButerin",
        "elonmusk",
        "solana",
        "cz_binance"
    ]