import logging
import json
import os
from datetime import datetime
import pytz
from typing import List
from src.app_config import Config

# Configure Structured Logging
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_activity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_working_hours() -> bool:
    """
    Checks if current time is within the defined working schedule.
    Returns:
        bool: True if within working hours OR if DEV_MODE is active.
    """
    # 🚧 Developer Mode Check
    if Config.DEV_MODE:
        
        return True

    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Logic: Pause between 01:00 AM and 08:00 AM
    if 1 <= now.hour < Config.WORK_START_HOUR:
        return False
    return True
class StateManager:
    """
    Handles local persistence to prevent processing the same tweet twice.
    """
    DATA_FILE = "data/seen_tweets.json"

    @staticmethod
    def _ensure_dir():
        os.makedirs(os.path.dirname(StateManager.DATA_FILE), exist_ok=True)

    @staticmethod
    def load_seen_tweets() -> List[str]:
        if not os.path.exists(StateManager.DATA_FILE):
            return []
        try:
            with open(StateManager.DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.error("Failed to load seen tweets database. Starting fresh.")
            return []

    @staticmethod
    def save_tweet_id(tweet_id: str):
        StateManager._ensure_dir()
        seen = StateManager.load_seen_tweets()
        
        if tweet_id not in seen:
            seen.append(tweet_id)
            # Optimize: Keep only last 1000 entries to prevent file bloat
            if len(seen) > 1000:
                seen = seen[-1000:]
            
            with open(StateManager.DATA_FILE, 'w') as f:
                json.dump(seen, f)
    
    @staticmethod
    def is_seen(tweet_id: str) -> bool:
        seen = StateManager.load_seen_tweets()
        return tweet_id in seen