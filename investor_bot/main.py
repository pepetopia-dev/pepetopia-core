import os
import logging
import pytz
from datetime import datetime, time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from diary_reader import DiaryReader

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
TELEGRAM_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")
DIARY_FILE_PATH: str = "project_diary.md"
TR_TIMEZONE = pytz.timezone("Europe/Istanbul")

# --- CORE LOGIC ---

async def get_daily_report_text() -> str | None:
    """
    Helper function to read the diary for the current day.
    Returns the formatted message or None.
    """
    try:
        reader = DiaryReader(DIARY_FILE_PATH)
        today_str = datetime.now(TR_TIMEZONE).strftime("%d.%m.%Y")
        entry_content = reader.get_entry_by_date(today_str)

        if entry_content:
            header = f"🐸 **PEPETOPIA GÜNLÜK RAPOR - {today_str}**\n\n"
            return header + entry_content
        return None
    except Exception as e:
        logger.error(f"Error reading diary: {e}")
        return None

# --- COMMAND HANDLERS (INTERACTIONS) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /start. Introduces the bot.
    """
    user_first_name = update.effective_user.first_name
    welcome_msg = (
        f"Merhaba {user_first_name}! 👋\n\n"
        "Ben **Pepetopia Asistanı**. Görevlerim şunlar:\n"
        "📅 Her gün 20:00'de proje günlüğünü sunmak.\n"
        "📢 Ekibin teknik gelişmelerini size aktarmak.\n\n"
        "Komutları görmek için /help yazabilirsin."
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /help. Lists available commands.
    """
    help_text = (
        "🤖 **Mevcut Komutlar:**\n\n"
        "/start - Botu başlatır ve tanışır.\n"
        "/now - (Admin) Bugünün raporunu anında gönderir.\n"
        "/status - Sistem durumunu ve sunucu saatini gösterir.\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /status. Checks server health.
    """
    server_time = datetime.now(TR_TIMEZONE).strftime("%d.%m.%Y %H:%M:%S")
    status_msg = (
        "✅ **Sistem Çalışıyor**\n"
        f"📍 **Sunucu Saati (TR):** `{server_time}`\n"
        "📂 **Veri Dosyası:** Bağlı"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def manual_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /now. Manually triggers the report sending.
    Useful for testing live in the group.
    """
    await update.message.reply_text("⏳ Rapor taranıyor, lütfen bekleyin...")
    
    report_text = await get_daily_report_text()
    
    if report_text:
        await update.message.reply_text(report_text, parse_mode='Markdown')
        logger.info("Manual report sent successfully.")
    else:
        await update.message.reply_text(
            "⚠️ **Uyarı:** Bugün (TR saatiyle) için henüz bir günlük girişi bulunamadı.",
            parse_mode='Markdown'
        )

# --- AUTOMATED JOBS ---

async def scheduled_report_job(context: ContextTypes.DEFAULT_TYPE):
    """
    The background job that runs automatically at 20:00.
    """
    logger.info("Running scheduled job...")
    report_text = await get_daily_report_text()
    
    if report_text and CHAT_ID:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=report_text,
            parse_mode='Markdown'
        )
    else:
        logger.warning("Scheduled job found no content or GROUP_ID is missing.")

# --- MAIN EXECUTION ---

def main():
    """
    Main entry point using ApplicationBuilder (The modern way).
    """
    if not TELEGRAM_TOKEN:
        logger.critical("Bot token is missing!")
        return

    # 1. Build the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # 2. Add Command Handlers (Interaction)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("now", manual_report_command))

    # 3. Setup Daily Schedule (Automation)
    # Using the built-in JobQueue instead of the 'schedule' library
    job_queue = application.job_queue
    
    # Schedule time: 20:00 Turkey Time
    target_time = time(hour=20, minute=0, tzinfo=TR_TIMEZONE)
    
    job_queue.run_daily(scheduled_report_job, time=target_time, days=(0, 1, 2, 3, 4, 5, 6))
    
    logger.info(f"Bot is live! Scheduled for {target_time} TRT.")

    # 4. Run the Bot
    # polling() keeps the script running and listening for commands
    application.run_polling()

if __name__ == "__main__":
    main()