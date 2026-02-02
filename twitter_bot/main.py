import logging
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
    Initial handshake. Checks security clearance.
    """
    user_id = str(update.effective_chat.id)
    
    if user_id != Config.TELEGRAM_CHAT_ID:
        logger.warning(f"⛔ Unauthorized access attempt: {user_id}")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=(
            "👋 **Pepetopia Strategic Core Online**\n\n"
            "I am initialized with the new **Link-Aware** and **Topic-Grounded** engine.\n"
            "Send me a tweet text or a direct link to analyze."
        ),
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main message handler.
    """
    user_id = str(update.effective_chat.id)
    
    if user_id != Config.TELEGRAM_CHAT_ID:
        return

    if not update.message or not update.message.text:
        await context.bot.send_message(chat_id=user_id, text="⚠️ Please send text or a link.")
        return

    incoming_text = update.message.text
    
    # Send feedback message
    status_msg = await context.bot.send_message(
        chat_id=user_id, 
        text="🧠 **Extracting Context & Analyzing...**"
    )

    # Execute AI Logic
    # (Note: Logic is encapsulated in ai_engine to keep main.py clean)
    ai_response = analyze_and_draft(incoming_text)

    # Update the status message with the result
    await context.bot.edit_message_text(
        chat_id=user_id,
        message_id=status_msg.message_id,
        text=ai_response,
        parse_mode='Markdown'
    )

def main():
    logger.info("🚀 Starting Pepetopia Bot Service...")
    
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    # Handle text messages that are NOT commands
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()