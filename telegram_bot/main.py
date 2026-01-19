"""
TOPI (Pepetopia Bot) - Main Entry Point
---------------------------------------
Author: Pepetopia Dev Team
Version: 1.0.3 (Render Fix Edition)
"""

import logging
import sys
import os

# --- PATH CONFIGURATION (CRITICAL FIX) ---

current_dir = os.path.dirname(os.path.abspath(__file__))

src_dir = os.path.join(current_dir, "src")


if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


print(f"📂 Sys Path Adjusted: {sys.path}")
# -----------------------------------------

from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)

# --- IMPORTS ---

try:
    
    from core.config import Config
    from handlers.basic import start_command, help_command, ca_command, socials_command
    from handlers.crypto import price_command
    from handlers.ai_chat import ai_chat_handler
    from handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
    from handlers.security import welcome_new_member, verify_callback
    from handlers.moderation import moderation_handler, lockdown_command, unlock_command
    print("✅ Imports successful via Direct Path (e.g., 'from core...').")

except ImportError:
    print("⚠️ Direct import failed. Trying 'src.' prefix...")
    try:
        
        from src.core.config import Config
        from src.handlers.basic import start_command, help_command, ca_command, socials_command
        from src.handlers.crypto import price_command
        from src.handlers.ai_chat import ai_chat_handler
        from src.handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
        from src.handlers.security import welcome_new_member, verify_callback
        from src.handlers.moderation import moderation_handler, lockdown_command, unlock_command
        print("✅ Imports successful via 'src.' Prefix.")
    except ImportError as e:
        print("❌ CRITICAL IMPORT ERROR! Could not find modules.")
        print(f"Details: {e}")
        
        try:
            print(f"📂 Files in {src_dir}: {os.listdir(src_dir)}")
        except:
            print(f"⚠️ Could not list files in {src_dir}")
        raise e

# Keep Alive (Render Web Service için)
try:
    from keep_alive import keep_alive
except ImportError:
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
    Initializes the bot application.
    """
    try:
        logger.info("🚀 Initializing Pepetopia Bot (TOPI)...")
        
        if not Config.TELEGRAM_TOKEN:
            logger.critical("❌ TELEGRAM_TOKEN is missing! Check Environment Variables.")
            return

        # 1. Build Application
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # --- HANDLERS ---
        # Public Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("ca", ca_command))
        application.add_handler(CommandHandler("contract", ca_command)) 
        application.add_handler(CommandHandler("socials", socials_command))
        application.add_handler(CommandHandler("website", socials_command))

        # Admin Commands
        application.add_handler(CommandHandler("lockdown", lockdown_command))
        application.add_handler(CommandHandler("unlock", unlock_command))
        application.add_handler(CommandHandler("autopilot_on", start_schedule_command))
        application.add_handler(CommandHandler("autopilot_off", stop_schedule_command))
        
        # Security & Gatekeeping
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
        
        # Message Pipelines
        # Group 1: Moderation
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), moderation_handler), group=1)
        # Group 2: AI Chat
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler), group=2)

        # --- STARTUP ---
        logger.info("✅ Bot is ready and polling...")
        

        keep_alive()
        
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"🔥 Critical System Failure inside main: {e}")

if __name__ == "__main__":
    main()