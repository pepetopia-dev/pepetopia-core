import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from src.core.config import Config
# Import our new handlers
from src.handlers.basic import start_command, help_command
from src.handlers.crypto import price_command

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
        logger.info("Initializing Pepetopia Bot...")
        
        # 1. Build the Application using the secure Token
        application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()
        
        # 2. Register Handlers (Commands)
        # When user types /start, run start_command function
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        # 3. Start the Bot
        logger.info("Bot is polling... (Press Ctrl+C to stop)")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Error: {e}")

if __name__ == "__main__":
    main()