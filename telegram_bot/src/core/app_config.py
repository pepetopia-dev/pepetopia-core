import os
from pathlib import Path
from dotenv import load_dotenv

# --- ABSOLUTE PATH FIX ---

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


load_dotenv(dotenv_path=ENV_PATH)

class Config:
    """
    Central configuration class.
    """
    
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TRADING_SYMBOL = os.getenv("TRADING_SYMBOL")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    @staticmethod
    def validate():
        
        print(f"--- DEBUG INFO ---")
        print(f"Looking for .env at: {ENV_PATH}")
        print(f"File exists?: {ENV_PATH.exists()}")
        print(f"TRADING_SYMBOL Value: '{Config.TRADING_SYMBOL}'")
        print(f"------------------")

        if not Config.TELEGRAM_TOKEN:
            raise ValueError("Error: TELEGRAM_TOKEN is missing.")
        if not Config.GEMINI_API_KEY:
            raise ValueError("Error: GEMINI_API_KEY is missing.")

# Run validation on import
Config.validate()