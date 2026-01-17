from telegram import Update
from telegram.ext import ContextTypes
from src.services.news_service import NewsService
from src.services.gemini_service import GeminiService
from src.services.market_service import MarketService
import logging
import datetime

logger = logging.getLogger(__name__)

# --- 09:00 & 18:00 NEWS DIGEST ---
async def news_digest_job(context: ContextTypes.DEFAULT_TYPE):
    """Morning and Evening News Digest"""
    news_batch = NewsService.get_recent_news(limit=7) # Get last 7 news
    if news_batch:
        # Ask Gemini to generate digest (In English)
        digest_text = await GeminiService.generate_daily_digest(news_batch)
        
        message = (
            f"🗞️ **TOPI DAILY DIGEST**\n\n"
            f"{digest_text}\n\n"
            f"📢 #Pepetopia #CryptoNews"
        )
        await context.bot.send_message(context.job.chat_id, text=message)

# --- 12:00 FEAR & GREED INDEX ---
async def fear_greed_job(context: ContextTypes.DEFAULT_TYPE):
    data = MarketService.get_fear_and_greed()
    if data:
        value = int(data['value'])
        status = data['value_classification']
        
        # Emoji and comment based on value
        if value < 25:
            emoji = "😨"
            comment = "The market is shivering! Is this a buying opportunity for the brave?"
        elif value > 75:
            emoji = "🤑"
            comment = "Everyone is too greedy, time to be careful!"
        else:
            emoji = "😐"
            comment = "Market is undecided, looking for a direction."

        message = (
            f"🧠 **MARKET PSYCHOLOGY (Fear & Greed)**\n\n"
            f"{emoji} **Status:** {status} ({value}/100)\n\n"
            f"💬 **TOPI's Comment:** {comment}\n"
            f"ℹ️ *This data measures the emotional state of investors. Extreme fear can be a bottom signal, extreme greed a top signal.*"
        )
        await context.bot.send_message(context.job.chat_id, text=message, parse_mode='Markdown')

# --- 14:00 TOP GAINERS ---
async def top_gainers_job(context: ContextTypes.DEFAULT_TYPE):
    coins = MarketService.get_top_gainers()
    if coins:
        list_text = ""
        for i, coin in enumerate(coins, 1):
            price = float(coin['current_price'])
            change = float(coin['price_change_percentage_24h'])
            list_text += f"{i}. **{coin['symbol'].upper()}**: ${price} (📈 +%{change:.2f})\n"
        
        message = (
            f"🚀 **TOP GAINERS (Top 100)**\n"
            f"Even if the market bleeds, these are flashing green:\n\n"
            f"{list_text}\n"
            f"🔥 *TOPI Radar*"
        )
        await context.bot.send_message(context.job.chat_id, text=message, parse_mode='Markdown')

# --- 16:00 LONG/SHORT RATIO ---
async def long_short_job(context: ContextTypes.DEFAULT_TYPE):
    data = MarketService.get_long_short_ratio("BTCUSDT")
    if data:
        long_ratio = float(data['longAccount']) * 100
        short_ratio = float(data['shortAccount']) * 100
        ls_ratio = float(data['longShortRatio'])
        
        bias = "BULLISH 🐂" if ls_ratio > 1 else "BEARISH 🐻"

        message = (
            f"⚖️ **LONG vs SHORT BATTLE (BTC)**\n\n"
            f"📈 **Long:** %{long_ratio:.1f}\n"
            f"📉 **Short:** %{short_ratio:.1f}\n"
            f"📊 **Ratio:** {ls_ratio}\n\n"
            f"🏆 **Current Bias:** {bias}\n"
            f"ℹ️ *Shows the weight of positions in Binance Futures.*"
        )
        await context.bot.send_message(context.job.chat_id, text=message, parse_mode='Markdown')

# --- SCHEDULE START COMMAND ---
async def start_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jq = context.job_queue
    
    # Clear old jobs to prevent duplication
    for job in jq.get_jobs_by_name(f"sched_{chat_id}"):
        job.schedule_removal()

    # Schedule Times (Assuming Server Time = Your Local Time)
    # If using cloud hosting, adjust for UTC offset (e.g. UTC is 3 hours behind Turkey)
    
    # 09:00 News Digest
    jq.run_daily(news_digest_job, datetime.time(9, 0), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 12:00 Fear & Greed
    jq.run_daily(fear_greed_job, datetime.time(12, 0), chat_id=chat_id, name=f"sched_{chat_id}")
    # Testing line (runs once immediately):
    jq.run_once(fear_greed_job, 5, chat_id=chat_id)

    # 14:00 Top Gainers
    jq.run_daily(top_gainers_job, datetime.time(14, 0), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 16:00 Long/Short
    jq.run_daily(long_short_job, datetime.time(16, 0), chat_id=chat_id, name=f"sched_{chat_id}")
    
    # 18:00 News Digest
    jq.run_daily(news_digest_job, datetime.time(18, 0), chat_id=chat_id, name=f"sched_{chat_id}")

    await update.message.reply_text(
        "✅ **Fully Automated Broadcast Started!**\n\n"
        "🕘 09:00 - Morning Digest\n"
        "🕛 12:00 - Market Psychology (Fear&Greed)\n"
        "🕑 14:00 - Top Gainers\n"
        "🕓 16:00 - Long/Short Ratio\n"
        "🕕 18:00 - Evening Digest\n\n"
        "🐸 TOPI is ready for duty!"
    )

async def stop_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for job in context.job_queue.get_jobs_by_name(f"sched_{chat_id}"):
        job.schedule_removal()
    await update.message.reply_text("🛑 All automated broadcasts stopped.")