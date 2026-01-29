import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """
    Centralized configuration management.
    Validates existence of required environment variables at startup.
    """

    def __init__(self):
        self._validate_env_vars()

    def _validate_env_vars(self):
        """Checks for required environment variables and exits if missing."""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "GITHUB_ACCESS_TOKEN",
            "GITHUB_REPO_NAME",
            "GEMINI_API_KEY"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print(f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file.")
            sys.exit(1)

    @property
    def telegram_token(self) -> str:
        return os.getenv("TELEGRAM_BOT_TOKEN")

    @property
    def telegram_chat_id(self) -> str:
        return os.getenv("TELEGRAM_CHAT_ID")

    @property
    def github_token(self) -> str:
        return os.getenv("GITHUB_ACCESS_TOKEN")

    @property
    def github_repo_name(self) -> str:
        """Format: 'username/repository_name'"""
        return os.getenv("GITHUB_REPO_NAME")

    @property
    def gemini_api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY")

# Create a singleton instance to be imported elsewhere
config = AppConfig()