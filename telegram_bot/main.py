"""
TOPI (Pepetopia Bot) - Main Entry Point
---------------------------------------
This module initializes the Telegram Bot application, registers all event handlers,
and starts the polling loop. It serves as the central nervous system of the bot.

Author: Pepetopia Dev Team
Version: 1.0.0
"""
# --- PATH FIX (CRITICAL) ---
import logging
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
# ---------------------------
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Debug: Render loglarında klasör yapısını görmek için
print(f"📂 Current Work Dir: {os.getcwd()}")
print(f"📂 Script Dir: {current_dir}")
print(f"📂 Sys Path: {sys.path}")
try:
    print(f"📂 Files in {current_dir}: {os.listdir(current_dir)}")
except Exception:
    pass
# ---------------------------

from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)

# --- IMPORT FIX ---
# src klasörünü bulamazsa alternatif yolları dener
try:
    # 1. Normal Import Denemesi
    from src.core.config import Config
    from src.handlers.basic import start_command, help_command, ca_command, socials_command
    from src.handlers.crypto import price_command
    from src.handlers.ai_chat import ai_chat_handler
    from src.handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
    from src.handlers.security import welcome_new_member, verify_callback
    from src.handlers.moderation import moderation_handler, lockdown_command, unlock_command
    print("✅ 'src' imports successful.")
except ModuleNotFoundError as e:
    print(f"⚠️ 'src' import failed ({e}). Trying fallback imports...")
    # 2. Eğer src klasörü yoksa ve klasörler dışarı çıkarılmışsa:
    try:
        from core.config import Config
        from handlers.basic import start_command, help_command, ca_command, socials_command
        from handlers.crypto import price_command
        from handlers.ai_chat import ai_chat_handler
        from handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
        from handlers.security import welcome_new_member, verify_callback
        from handlers.moderation import moderation_handler, lockdown_command, unlock_command
        print("✅ Fallback imports successful (Flattened structure detected).")
    except Exception as e2:
        print("❌ CRITICAL IMPORT ERROR! Could not find modules in 'src' or root.")
        print(f"Error 1: {e}")
        print(f"Error 2: {e2}")
        raise e2

# Keep Alive (Render Web Service için)
try:
    from keep_alive import keep_alive
except ImportError:
    # Eğer keep_alive.py bulunamazsa botun çökmesini engelle
    print("⚠️ keep_alive.py not found. Running without web server.")
    def keep_alive(): pass

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