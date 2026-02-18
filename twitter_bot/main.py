import logging
import sys
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import Conflict

# Local imports
from src.app_config import Config
from src.ai_engine import analyze_and_draft

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responds to /start command."""
    user_id = str(update.effective_chat.id)
    
    # Security check (Simple ID verification)
    if user_id != Config.TELEGRAM_CHAT_ID:
        logger.warning(f"⛔ Unauthorized access attempt: {user_id}")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=(
            "👋 <b>Pepetopia Twitter Bot (v2.0)</b>\n\n"
            "Sistem hazır. Analiz etmek istediğin tweet'i (link veya metin) gönder.\n\n"
            "Modlar:\n"
            "• <b>CEO Modu:</b> Standart metin gönderimi.\n"
            "• <b>Mühendis Modu:</b> Metnin içine <code>@pepetopia_dev</code> ekle."
        ),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming text messages."""
    user_id = str(update.effective_chat.id)
    
    # Security check
    if user_id != Config.TELEGRAM_CHAT_ID:
        return

    if not update.message or not update.message.text:
        return

    incoming_text = update.message.text
    
    # Send "Thinking..." status
    status_msg = await context.bot.send_message(
        chat_id=user_id, 
        text="🧠 <b>Analiz ediliyor...</b>",
        parse_mode=ParseMode.HTML
    )

    try:
        # ASYNC FIX: We await the function directly.
        # No more asyncio.to_thread wrapping needed because ai_engine is now native async.
        ai_response = await analyze_and_draft(incoming_text)
        
    except Exception as e:
        logger.error(f"Main Loop Error: {e}")
        ai_response = f"⚠️ <b>Sistem Hatası:</b> {str(e)}"

    # Edit the status message with the result
    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=status_msg.message_id,
            text=ai_response,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Telegram API Error (Edit Message): {e}")
        # Fallback: If edit fails (e.g. formatting error), send a new message without formatting to debug
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⚠️ Format Hatası oluştu. Ham veri:\n\n{ai_response}",
            parse_mode=None
        )

def main():
    """Main entry point."""
    logger.info("🚀 Starting Pepetopia Bot Service...")
    
    # Validate Config
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.critical("❌ Bot Token Missing!")
        sys.exit(1)

    # Build Application
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Register Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    try:
        logger.info("📡 Polling started...")
        application.run_polling(drop_pending_updates=True)
        
    except Conflict:
        logger.critical("🛑 CONFLICT ERROR: Another bot instance is running with the same token.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")

if __name__ == '__main__':
    main()