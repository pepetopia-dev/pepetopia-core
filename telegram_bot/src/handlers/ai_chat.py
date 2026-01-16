from telegram import Update
from telegram.ext import ContextTypes
from src.services.gemini_service import GeminiService
import logging

logger = logging.getLogger(__name__)

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles regular text messages. 
    Triggers AI only if the bot is mentioned, replied to, or in a private chat.
    """
    # Safety check: Ensure message and text exist
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    bot_username = context.bot.username
    chat_type = update.effective_chat.type

    # Check triggers
    is_private = chat_type == "private"
    is_mention = f"@{bot_username}" in user_text
    
    # Check if the message is a reply to the bot
    is_reply = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply = True

    # Logic: Respond if it's a private chat OR if explicitly triggered in a group
    if is_private or is_reply or is_mention:
        
        # UX: Send 'typing' action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Clean the text (remove the @mention part)
        cleaned_text = user_text.replace(f"@{bot_username}", "").strip()
        
        # If message is empty after cleaning (e.g. just "@BotName"), ignore or default
        if not cleaned_text:
            cleaned_text = "Hello!"

        logger.info(f"AI Triggered by User: {update.effective_user.id} in {chat_type}")

        # Get response from Gemini
        ai_response = await GeminiService.get_response(cleaned_text)
        
        # Send response
        # Using reply_text ensures the user gets a notification
        await update.message.reply_text(ai_response, parse_mode='Markdown')