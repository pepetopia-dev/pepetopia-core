import logging
import sys
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import Conflict
from src.app_config import Config
from src.ai_engine import analyze_and_draft

# Logging Ayarları
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    if user_id != Config.TELEGRAM_CHAT_ID:
        logger.warning(f"⛔ Unauthorized access attempt: {user_id}")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="👋 **Pepetopia Bot Online**\nSistemi yerel modda başlattım. Link veya metin gönderin.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    if user_id != Config.TELEGRAM_CHAT_ID:
        return

    if not update.message or not update.message.text:
        return

    incoming_text = update.message.text
    
    # Bilgi mesajı
    status_msg = await context.bot.send_message(
        chat_id=user_id, 
        text="🧠 **Analiz ediliyor...**"
    )

    # AI motorunu kilitlemeden (non-blocking) çalıştır
    try:
        ai_response = await asyncio.to_thread(analyze_and_draft, incoming_text)
    except Exception as e:
        ai_response = f"⚠️ Kritik Hata: {str(e)}"

    # Sonucu yaz
    await context.bot.edit_message_text(
        chat_id=user_id,
        message_id=status_msg.message_id,
        text=ai_response,
        parse_mode='Markdown'
    )

def main():
    logger.info("🚀 Starting Pepetopia Bot Service (Standalone Mode)...")
    
    # Application oluştur
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    try:
        # drop_pending_updates=True: Bot kapalıyken biriken eski mesajları yoksayar,
        # bu da başlangıçtaki "Conflict" riskini azaltır.
        logger.info("Polling başlatılıyor...")
        application.run_polling(drop_pending_updates=True)
        
    except Conflict:
        logger.critical("🛑 HATA: Aynı token ile çalışan başka bir bot var!")
        logger.critical("👉 Çözüm: Açık kalan diğer terminalleri kapatın veya sunucuyu (Heroku vb.) yeniden başlatın.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Beklenmeyen Hata: {e}")

if __name__ == '__main__':
    main()