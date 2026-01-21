import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Initialize Logger
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /start]
    Entry point for the bot. Displays the main dashboard with available features.
    Language: Strictly English.
    """
    user = update.effective_user
    logger.info(f"User {user.id} started the bot.")

    # Main Welcome Message
    await update.message.reply_text(
        f"🐸 **Hello {user.mention_markdown()}!**\n\n"
        "I am **TOPI**, the advanced AI guardian of Pepetopia! 🛡️\n"
        "I speak **ALL languages**. You can chat with me in Turkish, English, Spanish, etc.!\n\n"
        
        "🚀 **Core Commands:**\n"
        "• /price - Live Market Stats ($PEPETOPIA) 📈\n"
        "• /digest - ⚡ Flash Market Report (AI Powered) 🗞️\n"
        "• /socials - Official Links & Community 🌐\n"
        "• /ca - Contract Address 📜\n\n"
        
        "📡 **Auto-News Tools:**\n"
        "• /autopilot_on - Start Daily News Feed (Every 6h)\n"
        "• /autopilot_off - Stop Auto-News\n\n"
        
        "🛡️ **Admin Tools:**\n"
        "• /lockdown - 🚨 Lock Chat\n"
        "• /unlock - ✅ Unlock Chat\n\n"
        
        "🤖 **AI Companion:**\n"
        "Just tag me to chat! -> `@Pepetopia_Bot What is the sentiment?`\n"
        "Type /help for more info.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /help]
    Provides support information matching BotFather list.
    """
    help_text = (
        "🆘 **TOPI Help Center**\n\n"
        "**🤖 AI & Chat:**\n"
        "• Mention me (@Pepetopia_Bot) to ask anything!\n"
        "• I can analyze sentiment, roast portfolios, or explain crypto concepts.\n\n"
        
        "**📊 Market & Info:**\n"
        "• /price - See current price, volume, and 24h change.\n"
        "• /ca - Get the official contract address.\n"
        "• /socials - Website, Twitter, Telegram links.\n\n"
        
        "**🗞️ News & Updates:**\n"
        "• /digest - Get an instant AI summary of the market.\n"
        "• /autopilot_on - Turn on automatic news (every 6 hours).\n"
        "• /autopilot_off - Turn off automatic news.\n\n"
        
        "**🛡️ Security (Admins):**\n"
        "• /lockdown - Close chat for non-admins.\n"
        "• /unlock - Open chat for everyone.\n\n"
        "🔗 **Source Code:** https://github.com/pepetopia-dev/pepetopia-core"
    )
    await update.message.reply_text(help_text, disable_web_page_preview=True, parse_mode='Markdown')

async def ca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /ca or /contract]
    Returns the official Token Contract Address in monospace format for easy copying.
    """
    # Placeholder Contract Address (Update this before Mainnet launch)
    contract_address = "9kYJGVYTxYUVPw59hcnXG2Q6VsC1GbK4KkhHsdrDpump" 
    
    await update.message.reply_text(
        f"🐸 **Pepetopia Official Contract (CA):**\n\n"
        f"`{contract_address}`\n\n"
        "(Tap to copy) 📋",
        parse_mode='Markdown'
    )

async def socials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /socials or /website]
    Displays official social media links using Inline Buttons.
    """
    # Button Layout
    keyboard = [
        [
            InlineKeyboardButton("🌐 Website", url="https://pepe-topia.com/"),
            InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/pepetopiaa")
        ],
        [
            InlineKeyboardButton("🐸 Telegram", url="https://t.me/pepetopiaaa"),
            InlineKeyboardButton("🦎 CoinGecko", url="https://www.coingecko.com/en/coins/pepetopia")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚀 **Join the Pepetopia Movement!** 🚀\n\n"
        "Follow us on our official channels to stay updated with the latest news, memes, and burns! 🐸💚",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )