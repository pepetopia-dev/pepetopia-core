import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.core.config import Config

# Import Handlers
from src.handlers.basic import start_command, help_command
from src.handlers.crypto import price_command
from src.handlers.ai_chat import ai_chat_handler  # NEW: Import the AI handler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point. Initializes the bot application and registers handlers.
    """
    try:
        logger.info("Initializing Pepetopia Bot (TOPI)...")
        
        # 1. Build the Application using the secure Token
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # 2. Register Handlers (Commands)
        # It is important to register specific commands first.
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        
        # 3. Register AI Chat Handler
        # This MUST be the last handler. It catches all text messages that are NOT commands.
        # If you put this above commands, it might try to reply to commands as text.
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler))

        # 4. Start the Bot
        logger.info("Bot is polling... (Press Ctrl+C to stop)")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Error: {e}")

if __name__ == "__main__":
    main()