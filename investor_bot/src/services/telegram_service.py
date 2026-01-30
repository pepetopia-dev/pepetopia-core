"""
Telegram Service Module

Provides integration with Telegram Bot API for sending messages
and handling bot commands. Manages the bot lifecycle including
polling for updates and message delivery.

Author: Pepetopia Development Team
"""

import sys
from typing import TYPE_CHECKING, Any, Optional

import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from src.app_config import config
from src.utils.logger import get_logger


# Type checking import to avoid circular dependency
if TYPE_CHECKING:
    from main import InvestorBot


# Initialize module logger
logger = get_logger(__name__)


class TelegramService:
    """
    Service for Telegram bot operations.
    
    Handles bot initialization, command registration, message sending,
    and polling for updates. Supports integration with the main bot
    instance for command-triggered operations.
    
    Attributes:
        chat_id: Target chat/channel ID for message delivery
        main_bot: Reference to the main InvestorBot instance
        application: Telegram bot application instance
    """
    
    def __init__(self, main_bot_instance: Optional["InvestorBot"] = None):
        """
        Initializes the Telegram service with bot configuration.
        
        Args:
            main_bot_instance: Optional reference to the main bot for
                              command-triggered operations
                              
        Raises:
            SystemExit: If Telegram bot token is not configured
        """
        if not config.telegram_token:
            logger.critical("Telegram Bot Token is missing")
            sys.exit(1)
        
        self.chat_id = config.telegram_chat_id
        self.main_bot = main_bot_instance
        
        # Build the application
        self.application = ApplicationBuilder().token(config.telegram_token).build()
        
        # Register command handlers
        self._register_handlers()
        
        logger.info("TelegramService initialized successfully")
    
    def _register_handlers(self) -> None:
        """
        Registers all command handlers for the bot.
        
        Commands:
            /start - Confirms bot is active
            /trigger - Manually triggers the daily report process
        """
        self.application.add_handler(
            CommandHandler("start", self._handle_start_command)
        )
        self.application.add_handler(
            CommandHandler("trigger", self._handle_trigger_command)
        )
        
        logger.debug("Command handlers registered")
    
    async def start_polling(self) -> None:
        """
        Starts the bot's polling mechanism for receiving updates.
        
        Initializes the application and begins polling for new
        messages and commands. Drops pending updates to avoid
        processing stale commands.
        """
        logger.info("Starting Telegram bot polling...")
        
        await self.application.initialize()
        await self.application.start()
        
        if self.application.updater:
            await self.application.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot polling started successfully")
        else:
            logger.error("Failed to start polling: Updater not available")
    
    async def stop_polling(self) -> None:
        """
        Gracefully stops the bot's polling mechanism.
        
        Should be called during application shutdown to ensure
        clean termination of the bot.
        """
        logger.info("Stopping Telegram bot polling...")
        
        if self.application.updater:
            await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        
        logger.info("Bot polling stopped")
    
    async def send_message(self, message: str) -> bool:
        """
        Sends a message to the configured chat/channel.
        
        Uses HTML parse mode for rich text formatting and disables
        web page preview for cleaner message display.
        
        Args:
            message: The message content to send (supports HTML formatting)
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=telegram.constants.ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.debug(f"Message sent successfully ({len(message)} chars)")
            return True
            
        except telegram.error.TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def _handle_start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handles the /start command.
        
        Sends a confirmation message indicating the bot is active.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        logger.info(f"Received /start command from user {update.effective_user.id if update.effective_user else 'unknown'}")
        
        if update.message:
            await update.message.reply_text(
                "🤖 Bot is active and ready to deliver development updates!"
            )
    
    async def _handle_trigger_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handles the /trigger command.
        
        Manually triggers the daily report generation process.
        Useful for testing or on-demand report generation.
        
        Args:
            update: Telegram update object
            context: Callback context
        """
        logger.info(f"Received /trigger command from user {update.effective_user.id if update.effective_user else 'unknown'}")
        
        if update.message:
            await update.message.reply_text(
                "🚀 Report generation process initiated..."
            )
        
        # Trigger the main bot's daily task if available
        if self.main_bot:
            try:
                await self.main_bot.run_daily_task()
                logger.info("Manual trigger completed successfully")
            except Exception as e:
                logger.error(f"Error during manual trigger: {e}")
                if update.message:
                    await update.message.reply_text(
                        "❌ An error occurred during report generation."
                    )
        else:
            logger.warning("Main bot instance not available for trigger")
