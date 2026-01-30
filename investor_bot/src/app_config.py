"""
Application Configuration Module

Centralized configuration management for the Investor Bot application.
Handles environment variable loading, validation, and provides type-safe
access to configuration values throughout the application.

Author: Pepetopia Development Team
"""

import os
import sys
from typing import List

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class AppConfig:
    """
    Centralized configuration management.
    
    Validates existence of required environment variables at startup
    and provides type-safe property access to configuration values.
    
    Raises:
        SystemExit: If required environment variables are missing
    """
    
    # List of required environment variables
    REQUIRED_VARS: List[str] = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "GITHUB_ACCESS_TOKEN",
        "GITHUB_REPO_NAME",
        "GEMINI_API_KEY"
    ]
    
    def __init__(self):
        """
        Initializes configuration and validates environment variables.
        """
        self._validate_env_vars()
    
    def _validate_env_vars(self) -> None:
        """
        Validates that all required environment variables are present.
        
        Raises:
            SystemExit: If any required variables are missing
        """
        missing_vars = [
            var for var in self.REQUIRED_VARS
            if not os.getenv(var)
        ]
        
        if missing_vars:
            print(f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file.")
            sys.exit(1)
    
    @property
    def telegram_token(self) -> str:
        """
        Returns the Telegram Bot API token.
        
        Returns:
            Telegram bot token string
        """
        return os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    @property
    def telegram_chat_id(self) -> str:
        """
        Returns the target Telegram chat/channel ID.
        
        Returns:
            Chat ID string
        """
        return os.getenv("TELEGRAM_CHAT_ID", "")
    
    @property
    def github_token(self) -> str:
        """
        Returns the GitHub personal access token.
        
        Returns:
            GitHub access token string
        """
        return os.getenv("GITHUB_ACCESS_TOKEN", "")
    
    @property
    def github_repo_name(self) -> str:
        """
        Returns the target GitHub repository name.
        
        Format: 'owner/repository_name'
        
        Returns:
            Repository name string
        """
        return os.getenv("GITHUB_REPO_NAME", "")
    
    @property
    def gemini_api_key(self) -> str:
        """
        Returns the Google Gemini API key.
        
        Returns:
            Gemini API key string
        """
        return os.getenv("GEMINI_API_KEY", "")


# Create a singleton instance to be imported elsewhere
config = AppConfig()
