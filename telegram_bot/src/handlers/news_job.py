from telegram import Update
from telegram.ext import ContextTypes
from src.services.news_service import NewsService
import logging

logger = logging.getLogger(__name__)

# Cache to store the last sent link to avoid duplicates
last_sent_link = None

async def news_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Periodic job to fetch and send news.
    """
    global last_sent_link
    
    # Fetch news
    news = NewsService.get_latest_news()
    
    if news:
        # Check if we already sent this news
        if news['link'] != last_sent_link:
            
            last_sent_link = news['link']
            
            # Format the message (English)
            message = (
                f"🚨 **BREAKING NEWS ({news['source']})**\n\n"
                f"📰 {news['title']}\n\n"
                f"👉 [Read More]({news['link']})\n\n"
                f"📢 #Crypto #Solana #Pepetopia"
            )
            
            # Get chat_id from the job context
            job = context.job
            await context.bot.send_message(job.chat_id, text=message, parse_mode='Markdown')
            logger.info(f"News sent: {news['title']}")
        else:
            logger.info("No new news found (duplicate).")
    else:
        logger.warning("Could not fetch any news.")

async def start_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to START the news feed in the current chat.
    Usage: /news_on
    """
    chat_id = update.effective_chat.id
    
    # Check if job already exists
    current_jobs = context.job_queue.get_jobs_by_name(f"news_job_{chat_id}")
    if current_jobs:
        await update.message.reply_text("📰 News feed is already active in this channel!")
        return

    # Schedule the job
    # interval=60 means check every 60 seconds (Good for testing)
    # Change to 300 or 600 later for production.
    context.job_queue.run_repeating(
        news_job, 
        interval=60, 
        first=10, 
        chat_id=chat_id, 
        name=f"news_job_{chat_id}"
    )
    
    await update.message.reply_text("✅ News feed started! I will scan the market every 60 seconds.")

async def stop_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to STOP the news feed.
    Usage: /news_off
    """
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(f"news_job_{chat_id}")
    
    if not current_jobs:
        await update.message.reply_text("⚠️ No active news feed found to stop.")
        return

    for job in current_jobs:
        job.schedule_removal()
    
    await update.message.reply_text("🛑 News feed stopped.")