import os
import sys
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    # dotenv not installed, assuming environment variables are set by the system
    pass

class Config:
    """
    Centralized configuration management.
    Validates essential environment variables at startup to prevent runtime failures.
    """

    # Retrieve keys safely
    # SECURITY NOTE: Never hardcode secrets in source code. Always use environment variables.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Telegram Chat ID (Strictly typed as string to avoid integer comparison issues)
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    @classmethod
    def validate(cls):
        """
        Validates that all required configuration variables are present.
        If a critical key is missing, the application will terminate immediately (Fail-Fast).
        """
        missing_keys = []
        if not cls.GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not cls.TELEGRAM_BOT_TOKEN:
            missing_keys.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            missing_keys.append("TELEGRAM_CHAT_ID")

        if missing_keys:
            # Critical Security Alert: Missing credentials
            print(f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_keys)}")
            print("Action: Please check your .env file.")
            # Only exit if not testing? No, explicit validation should fail.
            # But we won't call this on import anymore.
            sys.exit(1)