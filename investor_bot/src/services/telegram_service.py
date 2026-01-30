import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sys
from src.app_config import config

class TelegramService:
    def __init__(self, main_bot_instance=None):
        if not config.telegram_token:
            sys.exit(1)
        self.chat_id = config.telegram_chat_id
        self.main_bot = main_bot_instance
        self.application = ApplicationBuilder().token(config.telegram_token).build()
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("tetikle", self._cmd_trigger))

    async def start_polling(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)

    async def send_message(self, message: str):
        try:
            # HTML parse mode is more robust for our use case
            await self.application.bot.send_message(
                chat_id=self.chat_id, 
                text=message, 
                parse_mode=telegram.constants.ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"ERROR: Telegram send failed: {e}")

    async def _cmd_start(self, update, context):
        await update.message.reply_text("🤖 Bot aktif.")

    async def _cmd_trigger(self, update, context):
        await update.message.reply_text("🚀 Rapor süreci başlatıldı...")
        await self.main_bot.run_daily_task()