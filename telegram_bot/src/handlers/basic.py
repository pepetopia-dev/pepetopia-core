from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    Sends a welcome message to the user in English.
    """
    user = update.effective_user
    welcome_message = (
        f"🐸 **Hello {user.first_name}!**\n\n"
        "I am **Pepetopia Bot**. Here to serve the greenest and strongest community on Solana!\n\n"
        "🚀 **What can I do?**\n"
        "/price - Live $PEPETOPIA stats (Coming Soon)\n"
        "/meme - Get a random Pepe meme (Coming Soon)\n"
        "/ai - Chat with the Pepe AI (Coming Soon)\n\n"
        "I am currently under development. Stay tuned! 🌱"
    )
    
    # Send message with Markdown parsing
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /help command.
    """
    help_text = (
        "🆘 **Help Center**\n\n"
        "My systems are currently being built by the devs.\n"
        "If you encounter any issues, please report them on our GitHub.\n\n"
        "🔗 **GitHub:** https://github.com/pepetopia-dev/pepetopia-core"
    )
    await update.message.reply_text(help_text, disable_web_page_preview=True)