"""
TOPI (Pepetopia Bot) - Main Entry Point
---------------------------------------
Author: Pepetopia Dev Team
Version: 1.3.0 (Global Edition + Persistence)
"""

import logging
import sys
import os
import time

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
    # 1. Configuration
    from src.core.app_config import Config
    
    # 2. Handlers
    from src.handlers.basic import start_command, help_command, ca_command, socials_command
    from src.handlers.crypto import price_command
    from src.handlers.ai_chat import ai_chat_handler
    # Updated Imports for Persistence
    from src.handlers.scheduled_tasks import (
        start_schedule_command, 
        stop_schedule_command, 
        instant_news_command, 
        schedule_all_jobs  # Required for auto-start
    )
    from src.handlers.security import welcome_new_member, verify_callback
    from src.handlers.moderation import moderation_handler, lockdown_command, unlock_command

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

async def post_init(application):
    """
    Runs automatically after the bot starts.
    Restores the 'Autopilot' schedule for the main chat defined in .env.
    """
    main_chat_id = Config.MAIN_CHAT_ID
    
    if main_chat_id:
        try:
            # Ensure chat_id is an integer
            chat_id_int = int(main_chat_id)
            logger.info(f"🔄 Auto-Starting Autopilot for Main Chat ID: {chat_id_int}")
            
            # Restore the schedule (Istanbul Time)
            schedule_all_jobs(application.job_queue, chat_id_int)
            
            # Optional: Send a 'Bot is Online' message
            # await application.bot.send_message(chat_id=chat_id_int, text="🐸 TOPI is Online! Systems Active.")
            
        except Exception as e:
            logger.error(f"❌ Failed to auto-start autopilot: {e}")
    else:
        logger.warning("⚠️ MAIN_CHAT_ID not set in .env. Autopilot won't start automatically.")

def main():
    """
    Main execution function. Initializes the bot and starts polling.
    """
    try:
        logger.info("🚀 Initializing Pepetopia Bot (TOPI) - Global Edition...")
        
        # --- ZOMBIE KILLER PROTOCOL ---
        # Wait 5 seconds to ensure any previous instance is terminated on the server.
        logger.info("⏳ Waiting 5s for previous instance to terminate...")
        time.sleep(5)

        # Validate Configuration
        if not Config.TELEGRAM_TOKEN:
            logger.critical("❌ TELEGRAM_TOKEN is missing! Check Environment Variables.")
            return

        # Build Application with Post-Init Hook
        application = (
            ApplicationBuilder()
            .token(Config.TELEGRAM_TOKEN)
            .post_init(post_init) # <--- THIS ENABLES PERSISTENCE
            .build()
        )
        
        # --- REGISTER HANDLERS ---
        
        # 1. Basic & Info Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("socials", socials_command))
        application.add_handler(CommandHandler("website", socials_command))
        application.add_handler(CommandHandler("ca", ca_command))
        application.add_handler(CommandHandler("contract", ca_command)) 
        
        # 2. Market & News Commands
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("digest", instant_news_command))
        application.add_handler(CommandHandler("flash_news", instant_news_command))
        
        # 3. Admin & Automation Commands
        application.add_handler(CommandHandler("lockdown", lockdown_command))
        application.add_handler(CommandHandler("unlock", unlock_command))
        application.add_handler(CommandHandler("autopilot_on", start_schedule_command))
        application.add_handler(CommandHandler("autopilot_off", stop_schedule_command))
        
        # 4. Security (Gatekeeper)
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
        
        # 5. Message Processing (Moderation & AI)
        # Group 1: Moderation (Runs first)
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), moderation_handler), group=1)
        # Group 2: AI Chat (Runs if not stopped)
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler), group=2)

        logger.info("✅ Bot is ready and polling...")
        
        # Start Polling
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"🔥 Critical System Failure: {e}")

if __name__ == "__main__":
    main()