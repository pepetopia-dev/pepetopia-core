"""
TOPI (Pepetopia Bot) - Main Entry Point
---------------------------------------
This module initializes the Telegram Bot application, registers all event handlers,
and starts the polling loop. It serves as the central nervous system of the bot.

Author: Pepetopia Dev Team
Version: 1.0.0
"""
from keep_alive import keep_alive
import logging
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)
from src.core.config import Config

# --- IMPORT HANDLERS ---
# 1. Basic & Info Handlers
from src.handlers.basic import start_command, help_command, ca_command, socials_command
# 2. Crypto Data Handlers
from src.handlers.crypto import price_command
# 3. AI & Chat Handlers
from src.handlers.ai_chat import ai_chat_handler
# 4. Scheduled Tasks (Autopilot)
from src.handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
# 5. Security & Gatekeeping
from src.handlers.security import welcome_new_member, verify_callback
# 6. Moderation & Safety
from src.handlers.moderation import moderation_handler, lockdown_command, unlock_command

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """
    Initializes the bot application, registers handlers in priority order,
    and starts the polling loop.
    """
    try:
        logger.info("🚀 Initializing Pepetopia Bot (TOPI) Systems...")
        
        # 1. Build the Application using the secure Token from Config
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # --- HANDLER REGISTRATION ---

        # SECTION A: Public User Commands
        # -------------------------------
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        
        # Info Commands (with Aliases)
        application.add_handler(CommandHandler("ca", ca_command))
        application.add_handler(CommandHandler("contract", ca_command)) # Alias
        application.add_handler(CommandHandler("socials", socials_command))
        application.add_handler(CommandHandler("website", socials_command)) # Alias

        # SECTION B: Admin & Security Commands
        # ------------------------------------
        application.add_handler(CommandHandler("lockdown", lockdown_command))
        application.add_handler(CommandHandler("unlock", unlock_command))
        
        # Autopilot (News/Market Data Scheduler)
        application.add_handler(CommandHandler("autopilot_on", start_schedule_command))
        application.add_handler(CommandHandler("autopilot_off", stop_schedule_command))
        
        # SECTION C: Gatekeeping Events (High Priority)
        # ---------------------------------------------
        # 1. New Member Join Event -> Triggers Welcome & Mute
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        
        # 2. Captcha Button Click -> Verifies User
        application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
        
        # SECTION D: Message Pipelines (Text Analysis)
        # --------------------------------------------
        # We use 'groups' to allow multiple handlers to process the same text message independently.
        
        # Group 1: Moderation Layer (The Shield)
        # Checks for bad words, spam, and links. If a violation is found, it deletes the message
        # and stops propagation (using ApplicationHandlerStop).
        application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), moderation_handler), 
            group=1
        )
        
        # Group 2: AI Interaction Layer (The Brain)
        # If the message passes moderation (Group 1), it reaches here.
        # The AI decides whether to reply (if mentioned/DM) or stay silent.
        application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler), 
            group=2
        )

        # --- STARTUP ---
        logger.info("✅ Bot is ready and polling... (Press Ctrl+C to stop)")

        keep_alive()
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"🔥 Critical System Failure: {e}")

if __name__ == "__main__":
    main()