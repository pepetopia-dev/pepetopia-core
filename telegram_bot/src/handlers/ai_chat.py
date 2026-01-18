from telegram import Update
from telegram.ext import ContextTypes
from src.services.gemini_service import GeminiService
import logging

logger = logging.getLogger(__name__)

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Handler: AI Chat]
    Processes natural language messages.
    
    Triggers:
    - Direct Private Message (DM)
    - Mention in Group (@BotName)
    - Reply to Bot's message
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

        # Generate Response
        ai_response = await GeminiService.get_response(cleaned_text)
        
        # Send Reply
        await update.message.reply_text(ai_response, parse_mode='Markdown')