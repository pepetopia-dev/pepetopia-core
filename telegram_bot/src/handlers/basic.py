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
    # We emphasize the 'Polyglot' capability (speaking all languages).
    await update.message.reply_text(
        f"🐸 **Hello {user.mention_markdown()}!**\n\n"
        "I am **TOPI**, the advanced AI guardian of Pepetopia! 🛡️\n"
        "I speak **ALL languages**. You can chat with me in Turkish, English, Spanish, etc.!\n\n"
        
        "🚀 **Core Commands:**\n"
        "• /price - Live Market Stats ($PEPETOPIA) 📈\n"
        "• /digest - ⚡ Flash Market Report (AI Powered) 🗞️\n"
        "• /socials - Official Links & Community 🌐\n"
        "• /ca - Contract Address 💰\n"
        "• /autopilot_on - Start Daily News Feed 📡\n\n"
        
        "🛡️ **Admin Tools:**\n"
        "• /lockdown - 🚨 Emergency Lock\n"
        "• /unlock - ✅ Restore Chat\n\n"
        
        "🤖 **AI Companion:**\n"
        "Just tag me to chat! -> `@Pepetopia_Bot What is the sentiment?`",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /help]
    Provides support information.
    """
    help_text = (
        "🆘 **TOPI Help Center**\n\n"
        "**Available Features:**\n"
        "1. **AI Chat:** Mention me (@Pepetopia_Bot) to ask anything about crypto.\n"
        "2. **Market Data:** Use /price for live stats.\n"
        "3. **News:** Use /digest for an instant AI summary of the market.\n"
        "4. **Security:** I automatically mute spammers and verify new humans.\n\n"
        "🔗 **Source Code:** https://github.com/pepetopia-dev/pepetopia-core"
    )
    await update.message.reply_text(help_text, disable_web_page_preview=True, parse_mode='Markdown')

async def ca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /ca or /contract]
    Returns the official Token Contract Address in monospace format for easy copying.
    """
    # Placeholder Contract Address (Update this before Mainnet launch)
    contract_address = "7Xw...PEPETOPIA_CONTRACT_ADDRESS...SoL" 
    
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