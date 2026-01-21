import requests
from src.app_config import Config
from src.utils import logger

def send_telegram_alert(tweet_data: dict, ai_reply: str):
    """
    Sends a formatted HTML message to the specified Telegram Chat.
    """
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # HTML formatting for Telegram
    message = (
        f"🚨 <b>NEW TWEET DETECTED</b>\n\n"
        f"👤 <b>Author:</b> @{tweet_data['author']}\n"
        f"🕒 <b>Time:</b> {tweet_data['date']}\n\n"
        f"📝 <b>Original Tweet:</b>\n"
        f"<i>{tweet_data['content'][:200]}...</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>SUGGESTED REPLY (AI):</b>\n"
        f"<code>{ai_reply}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 <a href='{tweet_data['link']}'>Open Tweet</a>\n"
        f"<i>(Tap the code block to copy)</i>"
    )

    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Notification sent for tweet from @{tweet_data['author']}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification: {e}")