import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.services.news_service import NewsService
from src.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

# =========================================
# PART 1: THE WORKERS (News Generation)
# =========================================

async def instant_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /digest or /flash_news]
    Fetches news IMMEDIATELY, generates an AI summary, and sends it to the chat.
    """
    chat_id = update.effective_chat.id
    
    # 1. Send "Typing" action and status message
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    status_msg = await update.message.reply_text("🕵️‍♂️ **Scanning the market...**", parse_mode='Markdown')

    try:
        # 2. Fetch News (Last 6 items)
        news_batch = NewsService.get_recent_news(limit=6)
        
        if news_batch:
            # 3. AI Processing
            await context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=status_msg.message_id, 
                text="🧠 **TOPI is analyzing the data...**", 
                parse_mode='Markdown'
            )
            
            # Generate digest using Gemini
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            
            # 4. Final Output
            message = (
                f"⚡ **TOPI FLASH REPORT** ⚡\n\n"
                f"{digest_text}\n\n"
                f"📢 #Pepetopia #CryptoNews"
            )
            
            # Delete status message and send the fresh report
            await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
            await context.bot.send_message(chat_id=chat_id, text=message)
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=status_msg.message_id, 
                text="⚠️ No significant news found right now.", 
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Instant news command failed: {e}")
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text="⚠️ **System Error:** Could not fetch news.", 
            parse_mode='Markdown'
        )

async def news_digest_job(context: ContextTypes.DEFAULT_TYPE):
    """
    [Automated Job]
    This function is called by the JobQueue automatically.
    It fetches news and sends a digest to the specific chat.
    """
    job = context.job
    chat_id = job.chat_id
    
    try:
        news_batch = NewsService.get_recent_news(limit=7)
        
        if news_batch:
            digest_text = await GeminiService.generate_daily_digest(news_batch)
            message = (
                f"🗞️ **TOPI DAILY DIGEST**\n\n"
                f"{digest_text}\n\n"
                f"📢 #Pepetopia #CryptoNews"
            )
            await context.bot.send_message(chat_id=chat_id, text=message)
        else:
            logger.info(f"Scheduled digest skipped for {chat_id}: No news found.")
            
    except Exception as e:
        logger.error(f"Scheduled news job failed for {chat_id}: {e}")

# =========================================
# PART 2: THE MANAGERS (Schedule Controls)
# =========================================

async def start_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /autopilot_on]
    Activates the automatic news digest system.
    Schedule: Sends a summary every 6 hours (21600 seconds).
    """
    chat_id = update.effective_chat.id
    job_name = str(chat_id)

    # 1. Check if job already exists to prevent duplicates
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        await update.message.reply_text(
            "⚠️ **Autopilot is ALREADY active!**\n"
            "Relax, I'm already watching the market. 🔭",
            parse_mode='Markdown'
        )
        return

    # 2. Schedule the Job
    # We pass 'news_digest_job' (defined above) as the callback
    context.job_queue.run_repeating(
        news_digest_job,
        interval=21600, # 6 Hours
        first=10,       # First run in 10 seconds (Test run)
        chat_id=chat_id,
        name=job_name
    )

    logger.info(f"Autopilot started for chat {chat_id}")
    
    await update.message.reply_text(
        "🚀 **Autopilot ACTIVATED!**\n\n"
        "I will scan the market and post a **News Digest every 6 hours**. ⏱️\n"
        "First report coming in 10 seconds...",
        parse_mode='Markdown'
    )

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /autopilot_off]
    Stops the automatic news digest system.
    """
    chat_id = update.effective_chat.id
    job_name = str(chat_id)

    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if not current_jobs:
        await update.message.reply_text(
            "⚠️ **Autopilot is NOT active.**\n"
            "Use /autopilot_on to start.",
            parse_mode='Markdown'
        )
        return

    # Cancel all jobs for this chat
    for job in current_jobs:
        job.schedule_removal()

    logger.info(f"Autopilot stopped for chat {chat_id}")

    await update.message.reply_text(
        "🛑 **Autopilot DEACTIVATED.**\n"
        "I will no longer post automatic updates. You can still use /digest manually.",
        parse_mode='Markdown'
    )