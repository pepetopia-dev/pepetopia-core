import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Logger setup
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /start]
    Entry point for the bot. Displays the main dashboard with available features.
    
    Args:
        update (Update): Telegram update object.
        context (ContextTypes.DEFAULT_TYPE): Callback context.
    """
    user = update.effective_user
    logger.info(f"User {user.id} started the bot.")

    # Main Welcome Message
    # Note: Using Markdown parsing for bold/italic text
    await update.message.reply_text(
        f"🐸 **Hello {user.mention_markdown()}!**\n\n"
        "I am **TOPI**, the guardian and AI assistant of the Pepetopia Community! 🛡️\n"
        "How can I assist you today?\n\n"
        "🚀 **Community Commands:**\n"
        "• /price - Live Market Stats 📈\n"
        "• /ca - Contract Address (Copy-Paste) 💰\n"
        "• /socials - Official Links 🌐\n"
        "• /autopilot_on - Start AI News Feed (DM) 🗞️\n\n"
        "🛡️ **Security (Admins Only):**\n"
        "• /lockdown - 🚨 Emergency Lockdown\n"
        "• /unlock - ✅ Restore Chat\n\n"
        "🤖 **AI Companion:**\n"
        "To chat with me, just mention my name!\n"
        "Ex: `@Pepetopia_Bot Why is crypto dumping?`",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /help]
    Provides support information and links to the source code/docs.
    """
    help_text = (
        "🆘 **TOPI Help Center**\n\n"
        "I am an automated system designed to protect and entertain the Pepetopia community.\n"
        "If you encounter any bugs, please report them to the dev team.\n\n"
        "🔗 **Source Code:** https://github.com/pepetopia-dev/pepetopia-core"
    )
    await update.message.reply_text(help_text, disable_web_page_preview=True)

async def ca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /ca or /contract]
    Returns the official Token Contract Address in monospace format for easy copying.
    """
    # TODO: Replace with the actual Mainnet Contract Address before launch
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
    # Button Layout Configuration
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