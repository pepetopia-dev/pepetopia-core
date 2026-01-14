import logging
from src.core.config import Config

# Configure logging (English logs)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Pepetopia Bot.
    """
    try:
        logger.info("Starting Pepetopia Bot...")
        logger.info(f"Environment: {Config.ENVIRONMENT}")
        
        # Verify if keys are loaded (Do not print the actual keys!)
        if Config.TELEGRAM_TOKEN and Config.GEMINI_API_KEY:
            logger.info("Security Check: API Keys loaded successfully.")
        
        logger.info("Bot is ready to be built!")
        
    except Exception as e:
        logger.error(f"Critical Error: {e}")

if __name__ == "__main__":
    main()