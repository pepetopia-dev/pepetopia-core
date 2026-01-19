import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.services.price_service import PriceService
from src.core.app_config import Config

logger = logging.getLogger(__name__)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /price]
    Fetches and displays live trading data from AscendEX.
    """
    # Send 'Typing' action for better UX
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    symbol = Config.TRADING_SYMBOL
    logger.info(f"Requesting price for Symbol: '{symbol}'")

    if not symbol:
        await update.message.reply_text("⚠️ Configuration Error: Trading Symbol missing in .env")
        return

    # Fetch Data
    data = await PriceService.get_token_info(symbol)
    
    if data:
        # Data Parsing
        name = data['name']
        price = data['priceUsd']
        change_pct = data['changePercent']
        vol = data['volume']
        high = data['high']
        low = data['low']
        
        # Determine Trend Emoji
        trend_emoji = "🚀" if change_pct >= 0 else "🔻"
        
        # Build Message
        message = (
            f"🐸 **{name} (AscendEX)**\n\n"
            f"💰 **Price:** ${price:.8f}\n"
            f"{trend_emoji} **24h Change:** {change_pct:.2f}%\n\n"
            f"📊 **24h Volume:** {vol:,.2f}\n"
            f"📈 **24h High:** ${high:.8f}\n"
            f"📉 **24h Low:** ${low:.8f}\n\n"
            f"🔗 [Trade on AscendEX]({data['url']})"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        await update.message.reply_text(
            f"⚠️ **Data Unavailable**\n"
            f"Could not fetch data for pair `{symbol}` from AscendEX.\n"
            "Please check the symbol configuration."
        )