import logging
import time
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, ApplicationHandlerStop

logger = logging.getLogger(__name__)

# --- MODERATION CONFIGURATION ---

BAD_WORDS = [
    "scam", "rug", "fake", "honey", "drainer", 
    "free mint", "airdrop", "whitelist", "send funds", 
    "doubler", "risk free", "guaranteed"
]

WHITELIST_DOMAINS = [
    "pepetopia.com", "x.com", "twitter.com", 
    "t.me", "telegram.me", "coingecko.com", "dexscreener.com"
]

# --- SPAM (FLOOD) SETTINGS ---
# Stricter rules: 5 messages in 10 seconds = MUTE.
FLOOD_LIMIT = 5       
FLOOD_WINDOW = 10     
MUTE_DURATION = 300   # 5 Minutes Mute

# Flood storage: {user_id: [timestamp1, timestamp2]}
user_flood_log = {}

# Muted Permissions
RESTRICTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False
)

async def check_flood(user_id):
    """Checks message rate limit for a user."""
    current_time = time.time()
    if user_id not in user_flood_log:
        user_flood_log[user_id] = []
    
    # Keep timestamps within the window
    user_flood_log[user_id] = [t for t in user_flood_log[user_id] if t > current_time - FLOOD_WINDOW]
    user_flood_log[user_id].append(current_time)
    
    return len(user_flood_log[user_id]) > FLOOD_LIMIT

async def moderation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main Moderation Pipeline:
    1. Admin Immunity Check
    2. Flood/Spam Check
    3. Link & Bad Word Analysis
    """
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    chat = update.effective_chat
    
    # 1. ADMIN IMMUNITY
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ['creator', 'administrator']:
            return # Admins can do whatever they want
    except Exception:
        pass 

    # 2. FLOOD CONTROL
    if await check_flood(user.id):
        try:
            # Delete Spam
            await update.message.delete()
            
            # Mute User
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=RESTRICTED_PERMISSIONS,
                until_date=time.time() + MUTE_DURATION,
                use_independent_chat_permissions=True 
            )
            
            # Send Warning (Self-destructing message)
            warn = await context.bot.send_message(
                chat_id=chat.id,
                text=f"🚫 {user.mention_markdown()}, **SPAM DETECTED!** You are muted for 5 mins. ⏳",
                parse_mode='Markdown'
            )
            # Schedule warning deletion (requires JobQueue, or just leave it)
            
            logger.warning(f"User {user.id} muted for flooding.")
            raise ApplicationHandlerStop() # STOP PROCESSING
            
        except Exception as e:
            logger.error(f"Flood action failed (Bot likely not Admin): {e}")

    # 3. CONTENT ANALYSIS
    text = update.message.text.lower()
    violation = False
    
    # Link Filter
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type in ['url', 'text_link']:
                if not any(d in text for d in WHITELIST_DOMAINS):
                    violation = True
                    break
    
    # Bad Words Filter
    if not violation:
        for word in BAD_WORDS:
            if word in text:
                violation = True
                break

    # Action
    if violation:
        try:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"⚠️ {user.mention_markdown()}, **No unauthorized links/shilling!** 🛡️",
                parse_mode='Markdown'
            )
            raise ApplicationHandlerStop()
        except Exception:
            pass

# --- LOCKDOWN COMMANDS ---
async def lockdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Locks the chat for everyone except admins."""
    # (Existing implementation logic, just ensure comments are English)
    # ... [Keep your previous logic or ask if you need this refactored too]
    pass 
    # (Note: Assuming you kept the previous lockdown logic, just ensure it's imported in main)

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlocks the chat."""
    pass