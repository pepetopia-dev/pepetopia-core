"""
TOPI (Pepetopia Bot) - Main Entry Point
---------------------------------------
Author: Pepetopia Dev Team
Version: 1.0.6 (Production Release - Conflict Fix)
"""

import logging
import sys
import os
import time  # Required for the Zombie Killer delay

# --- PATH CONFIGURATION ---
# Ensures Python can find the 'src' directory regardless of execution context.
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")

# Add paths to system
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- IMPORTS ---
try:
    # Import Configuration
    from src.core.app_config import Config
    
    # Import Handlers
    from src.handlers.basic import start_command, help_command, ca_command, socials_command
    from src.handlers.crypto import price_command
    from src.handlers.ai_chat import ai_chat_handler
    from src.handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
    from src.handlers.security import welcome_new_member, verify_callback
    from src.handlers.moderation import moderation_handler, lockdown_command, unlock_command
    
    # Keep Alive Service (For Render Free Tier)
    try:
        from keep_alive import keep_alive
    except ImportError:
        def keep_alive(): pass

except ImportError as e:
    print(f"🔥 CRITICAL IMPORT ERROR: {e}")
    raise e

from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)

# --- LOGGING SETUP ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """
    Main execution function. Initializes the bot and starts polling.
    """
    try:
        logger.info("🚀 Initializing Pepetopia Bot (TOPI)...")
        
        # --- ZOMBIE KILLER PROTOCOL ---
        # Critical Fix for 'Conflict' Error:
        # We wait 10 seconds to ensure any previous instance (zombie process)
        # on Render is fully terminated before we start a new connection.
        logger.info("⏳ Waiting 10s for previous instance to terminate...")
        time.sleep(10)
        # ------------------------------

        # Validate Configuration
        if not Config.TELEGRAM_TOKEN:
            logger.critical("❌ TELEGRAM_TOKEN is missing! Check Environment Variables.")
            return

        # Build Application
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # --- REGISTER HANDLERS ---
        
        # 1. Public Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("ca", ca_command))
        application.add_handler(CommandHandler("contract", ca_command)) 
        application.add_handler(CommandHandler("socials", socials_command))
        application.add_handler(CommandHandler("website", socials_command))

        # 2. Admin & Automation Commands
        application.add_handler(CommandHandler("lockdown", lockdown_command))
        application.add_handler(CommandHandler("unlock", unlock_command))
        application.add_handler(CommandHandler("autopilot_on", start_schedule_command))
        application.add_handler(CommandHandler("autopilot_off", stop_schedule_command))
        
        # 3. Security (Gatekeeper)
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
        
        # 4. Message Processing (Moderation & AI)
        # Group 1: Moderation (Runs first, can stop propagation)
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), moderation_handler), group=1)
        # Group 2: AI Chat (Runs if not stopped by moderation)
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler), group=2)

        logger.info("✅ Bot is ready and polling...")
        
        # Start Fake Web Server (For Render)
        keep_alive()
        
        # Start Polling
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"🔥 Critical System Failure: {e}")

if __name__ == "__main__":
    main()