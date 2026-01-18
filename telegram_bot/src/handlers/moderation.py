import logging
import time
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, ApplicationHandlerStop

logger = logging.getLogger(__name__)

# --- MODERATION CONFIGURATION ---

# 1. Blacklist (Profanity & Scam Filters)
# All words must be lowercase for case-insensitive matching.
BAD_WORDS = [
    "scam", "rug", "fake", "honey", "drainer", 
    "free mint", "airdrop", "whitelist", 
    "dm me", "send funds", "make money", 
    "passive income", "giveaway", "doubler"
]

# 2. Whitelist (Allowed Domains)
WHITELIST_DOMAINS = [
    "pepetopia.com", "x.com", "twitter.com", 
    "t.me", "telegram.me", "coingecko.com", "dexscreener.com"
]

# 3. Anti-Flood (Spam) Settings
FLOOD_LIMIT = 5       # Max messages allowed...
FLOOD_WINDOW = 10     # ...within this many seconds
MUTE_DURATION = 600   # Penalty duration: 10 Minutes (in seconds)

# In-memory storage for flood tracking: {user_id: [timestamp1, timestamp2]}
user_flood_log = {}

# Permissions for Muted Users
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
    can_pin_messages=False
)

async def check_flood(user_id):
    """
    Checks if a user is exceeding the message rate limit.
    Returns: True if spam detected, False otherwise.
    """
    current_time = time.time()
    
    if user_id not in user_flood_log:
        user_flood_log[user_id] = []
    
    # Prune old logs (Keep only timestamps within the window)
    user_flood_log[user_id] = [t for t in user_flood_log[user_id] if t > current_time - FLOOD_WINDOW]
    
    # Add new message timestamp
    user_flood_log[user_id].append(current_time)
    
    # Check limit
    if len(user_flood_log[user_id]) > FLOOD_LIMIT:
        return True
    return False

async def moderation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Handler: Message Moderation]
    Pipeline:
    1. Admin Check (Bypass)
    2. Flood Control (Spam)
    3. Link Analysis (Anti-Ad)
    4. Text Analysis (Bad Words)
    """
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    
    # --- LEVEL 0: ADMIN IMMUNITY ---
    # Admins are exempt from all filters.
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        if member.status in ['creator', 'administrator']:
            return # Admin detected, exit moderation
    except Exception:
        pass # Fail safe

    # --- LEVEL 1: FLOOD CONTROL ---
    if await check_flood(user.id):
        try:
            # Mute the offender
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
                permissions=RESTRICTED_PERMISSIONS,
                until_date=time.time() + MUTE_DURATION,
                use_independent_chat_permissions=True 
            )
            
            # Delete message and warn
            await update.message.delete()
            await update.message.reply_text(
                f"🚫 {user.mention_markdown()}, **Stop spamming!** You are muted for 10 minutes. ⏳",
                parse_mode='Markdown'
            )
            logger.warning(f"User {user.id} muted for flooding.")
            
            # Stop propagation (Do not send to AI)
            raise ApplicationHandlerStop()
            
        except Exception as e:
            logger.error(f"Flood mute failed: {e}")

    # --- LEVEL 2: CONTENT ANALYSIS ---
    text = update.message.text.lower()
    violation_found = False
    
    # A) Anti-Link System
    has_link = False
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type in ['url', 'text_link']:
                has_link = True
                break
    
    if has_link:
        is_allowed = any(domain in text for domain in WHITELIST_DOMAINS)
        if not is_allowed:
            violation_found = True
            await update.message.reply_text(f"⚠️ {user.mention_markdown()}, **No unauthorized links allowed!** 🚫", parse_mode='Markdown')

    # B) Bad Words Filter
    if not violation_found:
        for word in BAD_WORDS:
            if word in text:
                violation_found = True
                await update.message.reply_text(f"🚫 {user.mention_markdown()}, **watch your language!** (Profanity/Shill detected)", parse_mode='Markdown')
                break

    # C) Action: Delete & Halt
    if violation_found:
        try:
            await update.message.delete()
        except Exception:
            pass
        # Stop propagation (Do not send to AI)
        raise ApplicationHandlerStop()

# --- PANIC MODE COMMANDS ---

async def lockdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /lockdown]
    Emergency Protocol: Locks the group completely. Only Admins can chat.
    """
    user = update.message.from_user
    chat = update.effective_chat

    # Verification
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ['creator', 'administrator']:
            return
    except:
        return

    # Apply Total Restriction
    permissions = ChatPermissions(
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
        can_pin_messages=False
    )

    try:
        await context.bot.set_chat_permissions(
            chat.id, 
            permissions,
            use_independent_chat_permissions=True
        )
        await update.message.reply_text(
            "🚨 **SECURITY LOCKDOWN ACTIVATED!** 🚨\n\n"
            "The chat has been temporarily **LOCKED** due to a detected threat.\n"
            "Please stand by while TOPI secures the perimeter. 🛡️\n\n"
            "*(Only Admins can chat now)*",
            parse_mode='Markdown'
        )
        logger.warning(f"Lockdown activated by {user.first_name} in {chat.title}")
    except Exception as e:
        logger.error(f"Lockdown failed: {e}")
        await update.message.reply_text("⚠️ **System Error:** Could not lock the chat. Check permissions.")


async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [Command: /unlock]
    Restores normal chat operations.
    """
    user = update.message.from_user
    chat = update.effective_chat

    # Verification
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ['creator', 'administrator']:
            return
    except:
        return

    # Restore Permissions
    permissions = ChatPermissions(
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
        can_pin_messages=False
    )

    try:
        await context.bot.set_chat_permissions(
            chat.id, 
            permissions,
            use_independent_chat_permissions=True
        )
        await update.message.reply_text(
            "✅ **SYSTEM NORMAL**\n\n"
            "Threat cleared. Chat has been **UNLOCKED**.\n"
            "Enjoy the vibes, Pepetopians! 🐸🚀",
            parse_mode='Markdown'
        )
        logger.info(f"Lockdown lifted by {user.first_name}")
    except Exception as e:
        logger.error(f"Unlock failed: {e}")
        await update.message.reply_text("⚠️ **System Error:** Could not unlock the chat.")