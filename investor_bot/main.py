import os
import logging
import pytz
import requests
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
DIARY_FILE_PATH: str = "data/project_diary.md"
TR_TIMEZONE = pytz.timezone("Europe/Istanbul")

# --- ASCENDEX CONFIGURATION ---
ASCENDEX_API_URL = "https://ascendex.com/api/pro/v1/spot/ticker"
SYMBOL = "PEPETOPIA/USDT"  # Borsa listeleme ismine göre burayı güncelleyebilirsin

# --- CORE LOGIC ---

def get_pepetopia_data() -> dict | None:
    """
    Fetches real-time price data from AscendEX API.
    Returns a dictionary with formatted data or None if failed.
    """
    try:
        params = {"symbol": SYMBOL}
        response = requests.get(ASCENDEX_API_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # AscendEX API response structure verification
# ... önceki kodlar ...
        if data.get('code') == 0 and 'data' in data:
            ticker = data['data']
            
            price = float(ticker.get('close', 0))
            open_price = float(ticker.get('open', 1))
            change_percent = ((price - open_price) / open_price) * 100
            
            # DÜZELTME: Token adedini fiyatla çarparak Dolar (USDT) hacmini buluyoruz
            token_volume = float(ticker.get('volume', 0))
            usd_volume = token_volume * price 
            
            return {
                "price": f"${price:.6f}",
                "change_percent": change_percent,
                "volume": f"${usd_volume:,.0f}" # Artık Dolar değeri olarak görünecek
            }
# ... kalan kodlar ...
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return None

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
    Responds to /start. Introduces the bot with the new Pepetopia manifesto.
    """
    user_first_name = update.effective_user.first_name
    
    welcome_msg = (
        f"Merhaba {user_first_name}! 👋\n\n"
        "🐸 **PepeTopia'ya Hoş Geldin!**\n\n"
        "**Nedir bu PepeTopia?**\n"
        "PepeTopia, Solana ağında \"bir meme coin daha\" olmak için değil, **topluluk odaklı değer üretmek** için doğdu. "
        "Bizim için başarı; anlık hype değil, şeffaflık ve uzun vadeli inşadır.\n\n"
        "**Bizi Farklı Kılan 3 Şey:**\n"
        "🌍 **Gerçek Yönetişim:** Token yakımından proje yönüne kadar kritik kararlar kapalı kapılar ardında değil, topluluk oylamasıyla alınır.\n"
        "🏛️ **PepeTopia Forum:** Algoritmaların değil, insanların yönettiği; derinlikli tartışmaların ve ortak aklın merkezi olan dijital evimizdir. (pepetopia-forum.com)\n"
        "🧠 **Yapay Zeka & Şeffaflık:** Açık kaynak kültürü ve TOPI gibi AI asistanlarıyla teknolojiyi merkeze alırız.\n\n"
        "**Benim Görevim Nedir?**\n"
        "Ben projenin **Yatırımcı İlişkileri Botuyum**. Teknik ekibin GitHub üzerinde yaptığı karmaşık kodlamaları her gün analiz eder, sadeleştirir ve raporlarım.\n\n"
        "_\"Precision takes time.\"_ ⏳\n\n"
        "Komutları görmek için: /help"
    )
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', disable_web_page_preview=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /help. Lists available commands.
    """
    # Not: Telegram Markdown modunda _ karakteri italik anlamına gelir ve hata yaratır.
    # Komutları ` (backtick) içine alarak bu sorunu çözüyoruz.
    help_text = (
        "🤖 *Mevcut Komutlar:*\n\n"
        "`/start` - Botu başlatır ve tanışır.\n"
        "`/anlik_fiyat` - Güncel AscendEX verilerini getirir.\n"
        "`/now` - (Admin) Bugünün raporunu anında gönderir.\n"
        "`/status` - Sistem durumunu ve sunucu saatini gösterir.\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /anlik_fiyat. Sends current market data.
    """
    data = get_pepetopia_data()
    
    if data:
        # Determine emoji based on trend
        trend_emoji = "🟢" if data['change_percent'] >= 0 else "🔴"
        
        msg = (
            f"📊 **Piyasa Durumu ({SYMBOL})**\n\n"
            f"💰 **Fiyat:** `{data['price']}`\n"
            f"{trend_emoji} **24s Değişim:** `%{data['change_percent']:.2f}`\n"
            f"📢 **Hacim:** `{data['volume']}`\n\n"
            f"🔗 _Veriler AscendEX üzerinden anlık çekilmiştir._"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Fiyat verisi şu an çekilemedi veya borsa API'si yanıt vermiyor.", parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /status. Checks server health and includes price if available.
    """
    server_time = datetime.now(TR_TIMEZONE).strftime("%d.%m.%Y %H:%M:%S")
    
    # Try to fetch price for status report (quick check)
    price_data = get_pepetopia_data()
    price_text = f"`{price_data['price']}`" if price_data else "Erişilemedi"
    
    status_msg = (
        "✅ **Sistem Çalışıyor**\n"
        f"📍 **Sunucu Saati (TR):** `{server_time}`\n"
        f"💲 **Anlık Fiyat:** {price_text}\n"
        "📂 **Veri Dosyası:** Bağlı"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def manual_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Responds to /now. Manually triggers the report sending.
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
        # Optional: Append price to the daily report
        price_data = get_pepetopia_data()
        if price_data:
            trend = "📈" if price_data['change_percent'] >= 0 else "📉"
            footer = (
                f"\n\n---\n"
                f"{trend} **Kapanış Bilgisi:** Fiyat: {price_data['price']} | Değişim: %{price_data['change_percent']:.2f}"
            )
            report_text += footer

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
    Main entry point using ApplicationBuilder.
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
    application.add_handler(CommandHandler("anlik_fiyat", price_command)) # New Command

    # 3. Setup Daily Schedule (Automation)
    job_queue = application.job_queue
    
    # Schedule time: 20:00 Turkey Time
    target_time = time(hour=20, minute=0, tzinfo=TR_TIMEZONE)
    
    job_queue.run_daily(scheduled_report_job, time=target_time, days=(0, 1, 2, 3, 4, 5, 6))
    
    logger.info(f"Bot is live! Scheduled for {target_time} TRT.")

    # 4. Run the Bot
    application.run_polling()

if __name__ == "__main__":
    main()