import telegram
import asyncio
import sys
from src.app_config import config

class TelegramService:
    """
    Handles interactions with the Telegram Bot API.
    Uses asynchronous methods as required by python-telegram-bot v20+.
    """

    def __init__(self):
        if not config.telegram_token or not config.telegram_chat_id:
            print("ERROR: Telegram credentials missing.")
            sys.exit(1)
        
        self.bot = telegram.Bot(token=config.telegram_token)
        self.chat_id = config.telegram_chat_id

    async def send_message(self, message: str):
        try:
            print(f"INFO: Attempting to send message to {self.chat_id}...")
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            print("SUCCESS: Message sent to Telegram.")
        except telegram.error.TelegramError as e:
            print(f"ERROR: Failed to send Telegram message. Details: {e}")