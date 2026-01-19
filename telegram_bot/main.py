import logging
import sys
import os


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


try:
    from src.core.app_config import Config
    from src.handlers.basic import start_command, help_command, ca_command, socials_command
    from src.handlers.crypto import price_command
    from src.handlers.ai_chat import ai_chat_handler
    from src.handlers.scheduled_tasks import start_schedule_command, stop_schedule_command
    from src.handlers.security import welcome_new_member, verify_callback
    from src.handlers.moderation import moderation_handler, lockdown_command, unlock_command
    
    # Keep Alive 
    try:
        from keep_alive import keep_alive
    except ImportError:
        def keep_alive(): pass

except ImportError as e:
    logger.critical(f"🔥 IMPORT ERROR: {e}")
   
    debug_path = os.path.join(os.path.dirname(__file__), "src/core")
    try:
        logger.error(f"📂 Files in src/core: {os.listdir(debug_path)}")
    except:
        logger.error("📂 Could not list src/core")
    raise e

from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)

def main():
    try:
        logger.info("🚀 Initializing Pepetopia Bot (TOPI)...")
        
        if not Config.TELEGRAM_TOKEN:
            logger.critical("❌ TELEGRAM_TOKEN is missing!")
            return

        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # --- HANDLERS ---
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("ca", ca_command))
        application.add_handler(CommandHandler("contract", ca_command)) 
        application.add_handler(CommandHandler("socials", socials_command))
        application.add_handler(CommandHandler("website", socials_command))

        application.add_handler(CommandHandler("lockdown", lockdown_command))
        application.add_handler(CommandHandler("unlock", unlock_command))
        application.add_handler(CommandHandler("autopilot_on", start_schedule_command))
        application.add_handler(CommandHandler("autopilot_off", stop_schedule_command))
        
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_"))
        
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), moderation_handler), group=1)
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler), group=2)

        logger.info("✅ Bot is ready and polling...")
        keep_alive()
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"🔥 Critical Failure: {e}")

if __name__ == "__main__":
    main()