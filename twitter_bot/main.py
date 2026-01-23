import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from src.app_config import Config
from src.ai_engine import analyze_and_draft

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    Checks security (Chat ID) first.
    """
    user_id = str(update.effective_chat.id)
    
    # SECURITY CHECK: Only allow the admin defined in .env
    if user_id != Config.TELEGRAM_CHAT_ID:
        logger.warning(f"Unauthorized access attempt from ID: {user_id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Unauthorized access.")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=(
            "👋 **Pepetopia Strategic Advisor Online!**\n\n"
            "I am ready to hack the X Algorithm.\n"
            "Paste a tweet text or describe a context, and I will generate "
            "a high-ranking reply strategy based on 'SimClusters' and 'Reply Weight'."
        ),
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives text messages (Tweet content), sends to AI, and returns the strategy.
    """
    user_id = str(update.effective_chat.id)
    
    # SECURITY CHECK
    if user_id != Config.TELEGRAM_CHAT_ID:
        return

    incoming_text = update.message.text
    
    # User feedback: "Thinking..."
    processing_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="🧠 **Analyzing Algorithm Factors...**"
    )

    # Process with AI
    ai_response = analyze_and_draft(incoming_text)

    # Edit the "Thinking" message with the result
    # We use Markdown parsing for better readability, but need to be careful with AI output symbols.
    # For safety, we'll send as plain text or basic formatting.
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_msg.message_id,
        text=ai_response
    )

def main():
    """
    Main entry point for the Telegram Bot.
    """
    logger.info("🚀 Starting Pepetopia Strategic Advisor...")
    
    # Create the Application
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Add Handlers
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()