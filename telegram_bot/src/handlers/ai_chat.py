import sys
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# --- DYNAMIC IMPORT FOR TWITTER ENGINE ---
# This ensures we can import the refactored twitter_bot module
# without conflict with the local telegram_bot src package.
CORE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if CORE_ROOT not in sys.path:
    sys.path.append(CORE_ROOT)

from twitter_bot.src.ai_engine import analyze_and_draft

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Handler: AI Chat]
    Processes natural language messages using the Twitter Algorithm Insights Refactored Engine.
    """
    # Safety Check: Ignore empty updates or non-text messages
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    bot_username = context.bot.username
    chat_type = update.effective_chat.type

    # Determine Trigger Context
    is_private = chat_type == "private"
    is_mention = f"@{bot_username}" in user_text
    
    # Check for Reply
    is_reply = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply = True

    # Execution Logic
    if is_private or is_reply or is_mention:
        
        # UX: Indicate processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Sanitation: Remove the @BotName from the prompt
        cleaned_text = user_text.replace(f"@{bot_username}", "").strip()
        
        if not cleaned_text:
            cleaned_text = "Hello!"

        logger.info(f"AI Interaction triggered by User {update.effective_user.id} in {chat_type}")

        # Generate Response using the Refactored Twitter Engine
        # We run it in a thread since it's synchronous IO (mostly)
        try:
            ai_response = await asyncio.to_thread(analyze_and_draft, cleaned_text)
            
            # The ai_response string ALREADY contains the formatted output with 
            # Viral Score and Analysis logic as part of the string returned by ai_engine.format_response
            
        except Exception as e:
            logger.error(f"Failed to generate response via Algorithm Engine: {e}")
            ai_response = "⚠️ Engine Malfunction. Please try again later."
        
        # Send Reply
        await update.message.reply_text(ai_response, parse_mode='Markdown')