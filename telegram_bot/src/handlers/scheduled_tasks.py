from telegram import Update
from telegram.ext import ContextTypes
from src.services.news_service import NewsService
from src.services.gemini_service import GeminiService
from src.services.market_service import MarketService
import logging
import datetime
import pytz  # Required for accurate timezone scheduling

logger = logging.getLogger(__name__)

# --- TIMEZONE CONFIGURATION ---
# We explicitly set the timezone to Istanbul (UTC+3) to ensure
# the bot runs at the correct local time regardless of the server location.
TARGET_TIMEZONE = pytz.timezone("Europe/Istanbul")

# --- 09:00 & 18:00: NEWS DIGEST JOB ---
async def news_digest_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Scheduled Job: Fetches news and generates an AI summary.
    Runs twice daily (Morning/Evening).
    """
    try:
        # Fetch 7 mixed news items
        news_batch = NewsService.get_recent_news(limit=7)
        
        if news_batch:
            # Generate witty summary using Gemini AI
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            
            message = (
                f"🗞️ **TOPI DAILY DIGEST**\n\n"
                f"{digest_text}\n\n"
                f"📢 #Pepetopia #CryptoNews"
            )
            await context.bot.send_message(context.job.chat_id, text=message)
            logger.info("News digest sent successfully.")
        else:
            logger.warning("Skipping News Digest: No news found.")
            
    except Exception as e:
        logger.error(f"Error in news_digest_job: {e}")

# --- 12:00: FEAR & GREED INDEX JOB ---
async def fear_greed_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Scheduled Job: Fetches and displays the Market Fear & Greed Index.
    """
    try:
        data = MarketService.get_fear_and_greed()
        if data:
            value = int(data['value'])
            status = data['value_classification']
            
            # Dynamic commentary based on the index value
            if value < 25:
                emoji = "😨"
                comment = "Market is shivering! Is this a buying opportunity for the brave?"
            elif value > 75:
                emoji = "🤑"
                comment = "Extreme Greed detected! Be careful, anon."
            else:
                emoji = "😐"
                comment = "Market is undecided, waiting for a catalyst."

            message = (
                f"🧠 **MARKET PSYCHOLOGY (Fear & Greed)**\n\n"
                f"{emoji} **Status:** {status} ({value}/100)\n\n"
                f"💬 **TOPI's Insight:** {comment}\n"
                f"ℹ️ *This metric analyzes emotions and sentiments from different sources.*"
            )
            await context.bot.send_message(context.job.chat_id, text=message, parse_mode='Markdown')
        else:
            logger.warning("Fear & Greed data unavailable.")
            
    except Exception as e:
        logger.error(f"Error in fear_greed_job: {e}")

# --- 14:00: TOP GAINERS JOB ---
async def top_gainers_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Scheduled Job: Lists the top 5 performing coins from the top 100.
    """
    try:
        coins = MarketService.get_top_gainers()
        if coins:
            list_text = ""
            for i, coin in enumerate(coins, 1):
                price = float(coin['current_price'])
                change = float(coin['price_change_percentage_24h'])
                # Using upper() for symbol to look professional
                list_text += f"{i}. **{coin['symbol'].upper()}**: ${price} (📈 +%{change:.2f})\n"
            
            message = (
                f"🚀 **MARKET MOVERS (Top 100)**\n"
                f"While the market sleeps, these gems are pumping:\n\n"
                f"{list_text}\n"
                f"🔥 *TOPI Radar System*"
            )
            await context.bot.send_message(context.job.chat_id, text=message, parse_mode='Markdown')
        else:
            logger.warning("Top Gainers data unavailable.")

    except Exception as e:
        logger.error(f"Error in top_gainers_job: {e}")

# --- 16:00: LONG/SHORT RATIO JOB ---
async def long_short_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Scheduled Job: Fetches Binance Futures Long/Short ratio for BTC.
    """
    try:
        data = MarketService.get_long_short_ratio("BTCUSDT")
        if data:
            long_ratio = float(data['longAccount']) * 100
            short_ratio = float(data['shortAccount']) * 100
            ls_ratio = float(data['longShortRatio'])
            
            # Determine market bias
            bias = "BULLISH 🐂" if ls_ratio > 1 else "BEARISH 🐻"

            message = (
                f"⚖️ **LONG vs SHORT BATTLE (BTC)**\n\n"
                f"📈 **Long:** %{long_ratio:.1f}\n"
                f"📉 **Short:** %{short_ratio:.1f}\n"
                f"📊 **Ratio:** {ls_ratio}\n\n"
                f"🏆 **Current Bias:** {bias}\n"
                f"ℹ️ *Data source: Binance Futures Global Accounts*"
            )
            await context.bot.send_message(context.job.chat_id, text=message, parse_mode='Markdown')
        else:
            logger.warning("Long/Short data unavailable.")

    except Exception as e:
        logger.error(f"Error in long_short_job: {e}")

# --- COMMAND HANDLERS ---

async def start_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /autopilot_on]
    Activates the automated broadcast schedule for the current chat.
    Clears any existing jobs to prevent duplicates.
    """
    chat_id = update.effective_chat.id
    jq = context.job_queue
    
    # Step 1: Clean up old jobs for this chat
    existing_jobs = jq.get_jobs_by_name(f"sched_{chat_id}")
    for job in existing_jobs:
        job.schedule_removal()
    
    if existing_jobs:
        logger.info(f"Removed {len(existing_jobs)} old jobs for chat {chat_id}.")

    # Step 2: Schedule new jobs with Timezone Awareness
    # We use .replace(tzinfo=...) or datetime.time(..., tzinfo=...)
    
    # 09:00 Morning News
    jq.run_daily(news_digest_job, datetime.time(9, 0, tzinfo=TARGET_TIMEZONE), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 12:00 Market Sentiment
    jq.run_daily(fear_greed_job, datetime.time(12, 0, tzinfo=TARGET_TIMEZONE), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 14:00 Top Gainers
    jq.run_daily(top_gainers_job, datetime.time(14, 0, tzinfo=TARGET_TIMEZONE), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 16:00 Futures Ratio
    jq.run_daily(long_short_job, datetime.time(16, 0, tzinfo=TARGET_TIMEZONE), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 18:00 Evening News
    jq.run_daily(news_digest_job, datetime.time(18, 0, tzinfo=TARGET_TIMEZONE), chat_id=chat_id, name=f"sched_{chat_id}")

    await update.message.reply_text(
        "✅ **Autopilot Activated!**\n\n"
        "📅 **Daily Schedule (Turkey Time):**\n"
        "🕘 09:00 - Morning Digest\n"
        "🕛 12:00 - Fear & Greed Index\n"
        "🕑 14:00 - Top Gainers\n"
        "🕓 16:00 - Long/Short Ratio\n"
        "🕕 18:00 - Evening Digest\n\n"
        "🐸 TOPI is now monitoring the matrix."
    )

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /autopilot_off]
    Stops all automated broadcasts for this chat.
    """
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(f"sched_{chat_id}")
    
    for job in jobs:
        job.schedule_removal()
        
    await update.message.reply_text("🛑 **Autopilot Deactivated.** No more scheduled messages.")
    logger.info(f"Stopped {len(jobs)} jobs for chat {chat_id}.")