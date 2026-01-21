import logging
import datetime
import pytz
from telegram import Update
from telegram.ext import ContextTypes
from src.services.news_service import NewsService
from src.services.gemini_service import GeminiService
from src.services.market_service import MarketService

# Initialize Logger with standard naming convention
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Server Location: Frankfurt (Europe/Berlin)
# We align schedules to human activity in this timezone.
TIMEZONE_BERLIN = pytz.timezone("Europe/Berlin")

# =========================================
# SECTION 1: TASK HANDLERS (Workers)
# =========================================

async def instant_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /digest]
    Triggers an immediate AI-powered market news digest.
    Standard: Silicon Valley (High availability, user feedback).
    """
    chat_id = update.effective_chat.id
    
    # UX: Send typing action to indicate processing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # UX: Interim status message
    status_msg = await update.message.reply_text(
        "🕵️‍♂️ **Scanning the global market...**", 
        parse_mode='Markdown'
    )

    try:
        # Step 1: Fetch Data (Fail-safe)
        news_batch = NewsService.get_recent_news(limit=6)
        
        if news_batch:
            # Update status
            await context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=status_msg.message_id, 
                text="🧠 **TOPI is synthesizing intelligence...**", 
                parse_mode='Markdown'
            )
            
            # Step 2: AI Processing
            # Note: The prompt inside GeminiService must enforce English output.
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            
            # Step 3: Delivery
            # Using Markdown for bolding headers.
            message = (
                f"⚡ **TOPI FLASH REPORT** ⚡\n\n"
                f"{digest_text}\n\n"
                f"📢 #Pepetopia #CryptoNews"
            )
            
            # Cleanup status and send final report
            await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=status_msg.message_id, 
                text="⚠️ **System Notice:** No significant news found at this moment.", 
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Critical Error in instant_news_command: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text="⚠️ **System Error:** Unable to retrieve intelligence. Devs notified.", 
            parse_mode='Markdown'
        )

async def news_digest_job(context: ContextTypes.DEFAULT_TYPE):
    """
    [Scheduled Job]
    Fetches news, generates an AI summary, and broadcasts it.
    Differentiates between Morning and Evening editions.
    """
    job = context.job
    chat_id = job.chat_id
    
    try:
        # Fetch slightly more news for the daily digests
        news_batch = NewsService.get_recent_news(limit=8)
        
        if news_batch:
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            
            # Dynamic Title based on Job Name
            edition = "🌞 MORNING EDITION" if "morning" in job.name else "🌙 EVENING EDITION"
            
            message = (
                f"🗞️ **TOPI DAILY DIGEST | {edition}**\n\n"
                f"{digest_text}\n\n"
                f"📢 #Pepetopia #Crypto #Solana"
            )
            
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            logger.info(f"News digest ({edition}) sent to {chat_id}.")
        else:
            logger.warning(f"News digest skipped for {chat_id}: Empty news batch.")

    except Exception as e:
        logger.error(f"Job Execution Failed (news_digest_job): {e}", exc_info=True)

async def fear_greed_job(context: ContextTypes.DEFAULT_TYPE):
    """
    [Scheduled Job]
    Broadcasts the Crypto Fear & Greed Index.
    """
    job = context.job
    chat_id = job.chat_id
    
    try:
        data = MarketService.get_fear_and_greed()
        
        if data:
            value = int(data['value'])
            classification = data['value_classification']
            
            # AI Persona Logic (English)
            comment = "Market is undecided. Stay sharp."
            if value < 20: 
                comment = "🩸 Blood in the streets. A buying opportunity for the brave? 🤔"
            elif value < 40:
                comment = "😰 Fear is present. Weak hands are shaking."
            elif value > 75: 
                comment = "🤑 Extreme Greed! Careful, the top might be near. 📉"
            elif value > 60: 
                comment = "🚀 Sentiment is bullish! Don't FOMO blindly."

            msg = (
                f"🧠 **MARKET PSYCHOLOGY (Fear & Greed)**\n\n"
                f"📊 **Status:** `{classification}`\n"
                f"🔢 **Score:** `{value}/100`\n\n"
                f"🐸 **TOPI's Take:**\n_{comment}_"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Job Execution Failed (fear_greed_job): {e}")

async def top_gainers_job(context: ContextTypes.DEFAULT_TYPE):
    """
    [Scheduled Job]
    Broadcasts the Top 5 Gainer Coins (Top 100 MC).
    Strategy: Captures US Market open volatility (15:30 CET).
    """
    job = context.job
    chat_id = job.chat_id
    
    try:
        coins = MarketService.get_top_gainers()
        
        if coins:
            list_text = ""
            for i, coin in enumerate(coins):
                # Clean formatting for readability
                symbol = coin['symbol'].upper()
                price = coin['current_price']
                change = coin['price_change_percentage_24h']
                list_text += f"{i+1}. **{symbol}**: `${price}` (💚 +{change:.2f}%)\n"
            
            msg = (
                f"🚀 **MARKET MOVERS (Top 5)**\n"
                f"While the market sleeps, these gems are pumping:\n\n"
                f"{list_text}\n"
                f"🔥 *Powered by TOPI Radar*"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Job Execution Failed (top_gainers_job): {e}")

async def long_short_job(context: ContextTypes.DEFAULT_TYPE):
    """
    [Scheduled Job]
    Broadcasts BTC Long/Short Ratio from Binance Futures.
    """
    job = context.job
    chat_id = job.chat_id
    
    try:
        data = MarketService.get_long_short_ratio("BTCUSDT")
        
        if data:
            longs = float(data['longAccount']) * 100
            shorts = float(data['shortAccount']) * 100
            ratio = float(data['longShortRatio'])
            
            bias = "BULLISH 🐂" if ratio > 1 else "BEARISH 🐻"
            
            msg = (
                f"⚖️ **LONG vs SHORT BATTLE (BTC)**\n"
                f"Smart money positioning on Binance:\n\n"
                f"📈 **Longs:** `{longs:.1f}%`\n"
                f"📉 **Shorts:** `{shorts:.1f}%`\n"
                f"📊 **Ratio:** `{ratio}`\n\n"
                f"🏆 **Sentiment:** **{bias}**"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Job Execution Failed (long_short_job): {e}")

# =========================================
# SECTION 2: SCHEDULER CONTROLLER
# =========================================

async def start_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # --- SECURITY CHECK ---
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("🚫 **Access Denied:** Only Admins can control the Autopilot.", parse_mode='Markdown')
            return
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        return
    """
    [Command: /autopilot_on]
    Activates the "Autopilot" mode.
    Schedules 5 daily broadcasts aligned with Frankfurt (Berlin) time.
    """
    chat_id = update.effective_chat.id
    job_prefix = str(chat_id) 

    # Security: Remove existing jobs to prevent duplication/spam
    current_jobs = context.job_queue.get_jobs_by_name(job_prefix)
    for job in current_jobs:
        job.schedule_removal()

    # --- SCHEDULE CONFIGURATION (Berlin Time) ---
    
    # 08:30 - Morning Briefing (Start of day in EU)
    context.job_queue.run_daily(
        news_digest_job, 
        time=datetime.time(hour=8, minute=30, tzinfo=TIMEZONE_BERLIN), 
        chat_id=chat_id, 
        name=f"{job_prefix}_morning"
    )
    
    # 12:00 - Fear & Greed (Lunch break)
    context.job_queue.run_daily(
        fear_greed_job, 
        time=datetime.time(hour=12, minute=0, tzinfo=TIMEZONE_BERLIN), 
        chat_id=chat_id, 
        name=f"{job_prefix}_fng"
    )
    
    # 15:30 - Top Gainers (US Market Open - Volatility Spike)
    context.job_queue.run_daily(
        top_gainers_job, 
        time=datetime.time(hour=15, minute=30, tzinfo=TIMEZONE_BERLIN), 
        chat_id=chat_id, 
        name=f"{job_prefix}_gainers"
    )
    
    # 18:00 - Long/Short Ratio (End of work day in EU)
    context.job_queue.run_daily(
        long_short_job, 
        time=datetime.time(hour=18, minute=0, tzinfo=TIMEZONE_BERLIN), 
        chat_id=chat_id, 
        name=f"{job_prefix}_ls"
    )
    
    # 20:30 - Evening Digest (Review of the day)
    context.job_queue.run_daily(
        news_digest_job, 
        time=datetime.time(hour=20, minute=30, tzinfo=TIMEZONE_BERLIN), 
        chat_id=chat_id, 
        name=f"{job_prefix}_evening"
    )

    # Confirmation Message
    await update.message.reply_text(
        "✅ **Autopilot Activated! (Global Mode)**\n\n"
        "TOPI is now monitoring the market 24/7. Broadcast Schedule (Frankfurt Time):\n\n"
        "☕ **08:30** - Morning News\n"
        "😨 **12:00** - Fear & Greed Index\n"
        "🚀 **15:30** - Top Gainers (US Open)\n"
        "⚖️ **18:00** - Long/Short Ratio\n"
        "🌙 **20:30** - Evening Digest\n\n"
        "Sit back and relax, Fren. I got this. 🐸🛡️",
        parse_mode='Markdown'
    )
    logger.info(f"Autopilot started for chat {chat_id} with 5 daily jobs (Berlin Time).")

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # --- SECURITY CHECK ---
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("🚫 **Access Denied:** Only Admins can control the Autopilot.", parse_mode='Markdown')
            return
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        return
    """
    [Command: /autopilot_off]
    Deactivates all scheduled tasks for the chat.
    """
    chat_id = update.effective_chat.id
    job_prefix = str(chat_id)

    # Find jobs starting with the chat_id prefix
    current_jobs = [j for j in context.job_queue.jobs() if j.name and j.name.startswith(job_prefix)]

    if not current_jobs:
        await update.message.reply_text(
            "⚠️ **Autopilot is already OFF.**\n"
            "Use `/autopilot_on` to start the engine.",
            parse_mode='Markdown'
        )
        return

    for job in current_jobs:
        job.schedule_removal()

    logger.info(f"Autopilot stopped for chat {chat_id}")
    await update.message.reply_text(
        "🛑 **Autopilot Deactivated.**\n"
        "All automated broadcasts have been stopped. You can still use `/digest` manually.",
        parse_mode='Markdown'
    )