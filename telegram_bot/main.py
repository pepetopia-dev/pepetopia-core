import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.core.config import Config

# Import Handlers
from src.handlers.basic import start_command, help_command
from src.handlers.crypto import price_command
from src.handlers.ai_chat import ai_chat_handler
# YENİ: Sadece schedule (otopilot) komutlarını import ediyoruz
from src.handlers.scheduled_tasks import start_schedule_command, stop_schedule_command

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
        
        # 2. Register Command Handlers
        # Temel Komutlar
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("price", price_command))
        
        # Otopilot / Yayın Akışı Komutları (Eski news_on yerine bunlar geldi)
        application.add_handler(CommandHandler("autopilot_on", start_schedule_command))
        application.add_handler(CommandHandler("autopilot_off", stop_schedule_command))
        
        # 3. Register AI Chat Handler (MUST BE LAST)
        # Yapay zeka, yukarıdaki komutlara uymayan her şeyi yakalar.
        # Bu yüzden en sona koyuyoruz.
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_chat_handler))

        # 4. Start the Bot
        logger.info("Bot is polling... (Press Ctrl+C to stop)")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical Error: {e}")

if __name__ == "__main__":
    main()