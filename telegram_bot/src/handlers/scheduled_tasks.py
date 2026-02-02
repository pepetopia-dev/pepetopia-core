import logging
import datetime
import pytz
from telegram import Update
from telegram.ext import ContextTypes, JobQueue
from telegram.error import BadRequest, Forbidden
from src.services.news_service import NewsService
from src.services.gemini_service import GeminiService
from src.services.market_service import MarketService

# Initialize Logger
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Timezone: Istanbul (UTC+3)
TIMEZONE_TARGET = pytz.timezone("Europe/Istanbul")

# =========================================
# SECTION 1: TASK HANDLERS (Workers)
# =========================================

async def instant_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """[Command: /digest] Triggers an immediate digest."""
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    status_msg = await update.message.reply_text("🕵️‍♂️ **Scanning the market...**", parse_mode='Markdown')

    try:
        news_batch = await NewsService.get_recent_news(limit=6)
        if news_batch:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="🧠 **Synthesizing data...**", parse_mode='Markdown')
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            message = f"⚡ **TOPI FLASH REPORT** ⚡\n\n{digest_text}\n\n📢 #Pepetopia #CryptoNews"
            await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="⚠️ **System Notice:** No significant news found.", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in instant_news_command: {e}", exc_info=True)

async def news_digest_job(context: ContextTypes.DEFAULT_TYPE):
    """[Scheduled Job] Morning/Evening English Digest."""
    job = context.job
    chat_id = job.chat_id
    logger.info(f"Starting Major News Digest for Chat ID: {chat_id}")

    try:
        news_batch = await NewsService.get_recent_news(limit=8)
        if news_batch:
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            edition = "🌞 MORNING EDITION" if "morning" in str(job.name) else "🌙 EVENING EDITION"
            message = f"🗞️ **TOPI DAILY DIGEST | {edition}**\n\n{digest_text}\n\n📢 #Pepetopia #Crypto"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            logger.info(f"✅ Digest ({edition}) sent to {chat_id}.")
        else:
            logger.warning(f"Skipped digest for {chat_id}: No news.")
    except Exception as e:
        logger.error(f"Digest Job Failed: {e}")

async def flash_news_job(context: ContextTypes.DEFAULT_TYPE):
    """
    [Scheduled Job] Micro-Updates (TR/ES).
    Fetches 1 FRESH news item and summarizes it in Turkish & Spanish.
    """
    job = context.job
    chat_id = job.chat_id
    
    try:
        # Fetch just 1 latest news item
        news_batch = await NewsService.get_recent_news(limit=1)
        
        if news_batch:
            news_item = news_batch[0]
            # Generate Bilingual Summary
            flash_text = await GeminiService.generate_flash_update(news_item)
            
            message = (
                f"🚨 **TOPI FLASH INFO** 🚨\n\n"
                f"{flash_text}\n\n"
                f"🔗 [Source]({news_item['link']})"
            )
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
            logger.info(f"✅ Flash Update (TR/ES) sent to {chat_id}.")
        else:
            logger.info("Skipping Flash Update: No fresh news.")
            
    except Exception as e:
        logger.error(f"Flash News Job Failed: {e}")

async def fear_greed_job(context: ContextTypes.DEFAULT_TYPE):
    """[Scheduled Job] Fear & Greed Index."""
    job = context.job
    chat_id = job.chat_id
    try:
        data = MarketService.get_fear_and_greed()
        if data:
            value = int(data['value'])
            classification = data['value_classification']
            comment = "Market is undecided."
            if value < 25: comment = "Blood in the streets. Opportunity? 🤔"
            elif value > 75: comment = "Extreme Greed! Watch out. 📉"
            elif value > 60: comment = "Sentiment is bullish! 🚀"

            msg = f"🧠 **MARKET PSYCHOLOGY**\n\n📊 **Status:** `{classification}`\n🔢 **Score:** `{value}/100`\n\n🐸 **TOPI's Take:**\n_{comment}_"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"F&G Job Failed: {e}")

async def top_gainers_job(context: ContextTypes.DEFAULT_TYPE):
    """[Scheduled Job] Top Gainers."""
    job = context.job
    chat_id = job.chat_id
    try:
        coins = MarketService.get_top_gainers()
        if coins:
            list_text = ""
            for i, coin in enumerate(coins):
                list_text += f"{i+1}. **{coin['symbol'].upper()}**: `${coin['current_price']}` (💚 +{coin['price_change_percentage_24h']:.2f}%)\n"
            msg = f"🚀 **MARKET MOVERS (Top 5)**\n\n{list_text}\n🔥 *Powered by TOPI Radar*"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Gainers Job Failed: {e}")

async def long_short_job(context: ContextTypes.DEFAULT_TYPE):
    """[Scheduled Job] Long/Short Ratio."""
    job = context.job
    chat_id = job.chat_id
    try:
        data = MarketService.get_long_short_ratio("BTCUSDT")
        if data:
            longs = float(data['longAccount']) * 100
            shorts = float(data['shortAccount']) * 100
            ratio = float(data['longShortRatio'])
            bias = "BULLISH 🐂" if ratio > 1 else "BEARISH 🐻"
            msg = f"⚖️ **LONG vs SHORT (BTC)**\n\n📈 **Longs:** `{longs:.1f}%`\n📉 **Shorts:** `{shorts:.1f}%`\n📊 **Ratio:** `{ratio}`\n\n🏆 **Sentiment:** **{bias}**"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"L/S Job Failed: {e}")

# =========================================
# SECTION 2: SCHEDULER CONTROLLER
# =========================================

def schedule_all_jobs(job_queue: JobQueue, chat_id: int):
    """
    Central Scheduler.
    Now includes Micro-Updates (Flash Info) in TR/ES.
    """
    job_prefix = str(chat_id)
    
    # 1. Clean existing jobs
    current_jobs = job_queue.get_jobs_by_name(job_prefix)
    for job in current_jobs:
        job.schedule_removal()
        
    # --- MAJOR BROADCASTS (English) ---
    # 08:30 - Morning News
    job_queue.run_daily(news_digest_job, time=datetime.time(8, 30, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_morning")
    # 12:00 - Fear & Greed
    job_queue.run_daily(fear_greed_job, time=datetime.time(12, 0, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_fng")
    # 15:30 - Top Gainers
    job_queue.run_daily(top_gainers_job, time=datetime.time(15, 30, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_gainers")
    # 18:00 - Long/Short Ratio
    job_queue.run_daily(long_short_job, time=datetime.time(18, 0, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_ls")
    # 20:30 - Evening News
    job_queue.run_daily(news_digest_job, time=datetime.time(20, 30, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_evening")

    # --- MICRO UPDATES (TR/ES Flash Info) ---
    # Daytime Cycle
    job_queue.run_daily(flash_news_job, time=datetime.time(10, 0, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_flash_1")
    job_queue.run_daily(flash_news_job, time=datetime.time(13, 45, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_flash_2")
    job_queue.run_daily(flash_news_job, time=datetime.time(16, 45, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_flash_3")
    
    # Night Cycle
    job_queue.run_daily(flash_news_job, time=datetime.time(21, 45, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_flash_4")
    job_queue.run_daily(flash_news_job, time=datetime.time(23, 0, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_flash_5")
    job_queue.run_daily(flash_news_job, time=datetime.time(0, 15, tzinfo=TIMEZONE_TARGET), chat_id=chat_id, name=f"{job_prefix}_flash_6")
    
    logger.info(f"✅ All 11 jobs scheduled for chat {chat_id} (Major + Micro Updates).")

async def start_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activates Autopilot."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("🚫 Only Admins can control Autopilot.")
            return
    except Exception:
        return

    schedule_all_jobs(context.job_queue, chat_id)
    await update.message.reply_text("✅ **Autopilot V2 Activated!**\n\nTOPI is now broadcasting Major + Micro updates 24/7.", parse_mode='Markdown')

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deactivates Autopilot."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            return
    except Exception:
        return

    job_prefix = str(chat_id)
    current_jobs = [j for j in context.job_queue.jobs() if j.name and j.name.startswith(job_prefix)]
    for job in current_jobs:
        job.schedule_removal()
    
    await update.message.reply_text("🛑 **Autopilot Deactivated.**")