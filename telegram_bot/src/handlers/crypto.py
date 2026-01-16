import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.services.price_service import PriceService
from src.core.config import Config

logger = logging.getLogger(__name__)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /price command using AscendEX data.
    """
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    symbol = Config.TRADING_SYMBOL
    logger.info(f"DEBUG: Bot is requesting price for Symbol: '{symbol}'")

    if not symbol:
        await update.message.reply_text("⚠️ Trading Symbol not configured properly in .env")
        return

    data = await PriceService.get_token_info(symbol)
    
    if data:
        # Format Variables
        name = data['name']
        price = data['priceUsd']
        change_pct = data['changePercent']
        vol = data['volume']
        high = data['high']
        low = data['low']
        
        trend_emoji = "🚀" if change_pct >= 0 else "🔻"
        
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
        await update.message.reply_text("⚠️ Could not fetch data from AscendEX. Check the symbol in .env")