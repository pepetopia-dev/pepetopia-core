import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden

# Initialize Logger
logger = logging.getLogger(__name__)

# --- PERMISSIONS CONFIGURATION ---
# Protocol: Telegram API v21+ requires granular permission settings.

# 1. Restricted Mode (Muted)
# The user cannot send any type of content.
RESTRICTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_invite_users=False,
    can_change_info=False,
    can_pin_messages=False,
)

# 2. Verified Mode (Active Member)
# Restores standard chat privileges.
VERIFIED_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
    can_change_info=False, 
    can_pin_messages=False,
)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Event: New Chat Member]
    
    Logic:
    1. Detects new user.
    2. Checks if user is Bot/Admin (Skipped).
    3. If Regular User -> Restrict (Mute) immediately.
    4. Sends a Welcome Message with a CAPTCHA button.
    """
    # Filter: Ensure valid message update
    if not update.message or not update.message.new_chat_members:
        return

    for user in update.message.new_chat_members:
        # Step 1: Ignore Bots (except self)
        if user.is_bot:
            if user.id == context.bot.id:
                # Bot joined the group: Check permissions
                try:
                    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
                    if bot_member.can_restrict_members:
                        await update.message.reply_text("🐸 TOPI is online! Fortress Protocol Activated. 🛡️")
                    else:
                        await update.message.reply_text(
                            "⚠️ **System Alert:** I lack 'Restrict Members' permission.\n"
                            "Please promote me to Admin to enable security features."
                        )
                except Exception as e:
                    logger.error(f"Permission check failed: {e}")
            continue

        # Step 2: Admin Immunity Check
        # Admins should never be muted by the bot.
        try:
            member_info = await context.bot.get_chat_member(update.effective_chat.id, user.id)
            if member_info.status in ['creator', 'administrator']:
                logger.info(f"User {user.id} is Admin/Creator. Skipping verification.")
                await update.message.reply_text(
                    f"🫡 Welcome Boss {user.mention_markdown()}! Systems are operational.",
                    parse_mode='Markdown'
                )
                continue
        except Exception as e:
            logger.error(f"Failed to check admin status for {user.id}: {e}")

        # Step 3: Mute and Verify Logic
        try:
            logger.info(f"Initiating verification for user {user.id}...")
            
            # Apply Mute (Restrict)
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
                permissions=RESTRICTED_PERMISSIONS,
                use_independent_chat_permissions=True 
            )
            
            # Prepare Verification Button
            keyboard = [[InlineKeyboardButton("🐸 I am Human (Verify)", callback_data=f"verify_{user.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send Challenge Message
            await update.message.reply_text(
                f"🚨 **Security Alert** 🚨\n\n"
                f"Welcome {user.mention_markdown()}, Fren! 🐸\n\n"
                "To prevent bot raids, you are currently **muted**.\n"
                "Please click the button below to prove you are human.\n\n"
                "🛡️ *Protected by TOPI Security*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Forbidden as e:
            logger.critical(f"Permission Denied: Bot cannot restrict users. Error: {e}")
            await update.message.reply_text("⚠️ **Critical Error:** I need 'Ban Users' permission to function!")
        except Exception as e:
            logger.error(f"Unexpected error in welcome flow: {e}")


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Event: Callback Query]
    Handles the 'I am Human' button click.
    
    Logic:
    1. Validates that the clicker is the target user.
    2. Removes restrictions (Unmute).
    3. Updates the welcome message to a success state.
    """
    query = update.callback_query
    await query.answer() # Stop loading animation

    data = query.data
    try:
        action, target_user_id = data.split("_")
    except ValueError:
        return # Malformed data

    # Security Check: Prevent others from clicking the button
    if str(query.from_user.id) != str(target_user_id):
        await query.answer("❌ Access Denied: This button is not for you!", show_alert=True)
        return

    # Grant Access
    try:
        # Restore Permissions
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_user_id,
            permissions=VERIFIED_PERMISSIONS,
            use_independent_chat_permissions=True
        )

        # Update UI
        await query.edit_message_text(
            f"✅ **Verification Successful!**\n\n"
            f"Welcome to **Pepetopia**, {query.from_user.mention_markdown()}! 🚀\n"
            "You are now free to chat. WAGMI! 🐸",
            parse_mode='Markdown'
        )
        logger.info(f"User {target_user_id} verified successfully.")

    except Exception as e:
        logger.error(f"Verification failed for user {target_user_id}: {e}")
        await query.edit_message_text("⚠️ Error verifying user. Contact an Admin.")