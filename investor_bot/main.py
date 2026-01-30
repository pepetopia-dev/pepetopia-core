"""
Investor Bot - Main Application Entry Point

A Telegram bot that automatically generates and delivers non-technical
summaries of GitHub repository commits to stakeholders. Designed for
the Pepetopia community to keep investors informed about development
progress in an accessible, engaging format.

Features:
    - Automatic daily commit summarization
    - Multi-day update distribution for large commits
    - Manual trigger support via Telegram commands
    - Intelligent AI model selection with fallback

Author: Pepetopia Development Team
"""

import asyncio
import html
from datetime import datetime
from typing import Optional

import schedule

from src.services.github_service import GitHubService
from src.services.summarizer import CommitSummarizer
from src.services.telegram_service import TelegramService
from src.utils.logger import get_logger
from src.utils.persistence import PersistenceManager


# Initialize module logger
logger = get_logger("InvestorBot")


class InvestorBot:
    """
    Main application class orchestrating the investor update bot.
    
    Coordinates between GitHub, AI summarization, and Telegram services
    to deliver automated development updates to stakeholders.
    
    Attributes:
        github_service: Service for GitHub API interactions
        telegram_service: Service for Telegram bot operations
        summarizer: AI-powered commit summarization service
        persistence: State management for tracking progress
    """
    
    # Schedule time for daily updates (24-hour format)
    DAILY_UPDATE_TIME = "17:00"
    
    # Default author name for queued updates
    DEFAULT_AUTHOR = "Pepetopia Team"
    
    def __init__(self):
        """
        Initializes all bot services and components.
        """
        logger.info("Initializing Investor Bot...")
        
        self.github_service = GitHubService()
        self.telegram_service = TelegramService(main_bot_instance=self)
        self.summarizer = CommitSummarizer()
        self.persistence = PersistenceManager()
        
        logger.info("Investor Bot initialized successfully")
    
    async def run_daily_task(self) -> None:
        """
        Executes the daily update generation and delivery task.
        
        Workflow:
            1. Check for pending updates in queue
            2. If queue has items, send next queued update
            3. Otherwise, fetch and process new commits
            4. Generate AI summary and queue multi-part updates
            5. Deliver the first update immediately
        """
        logger.info(f"Running daily update task at {datetime.now().isoformat()}")
        
        # Step 1: Check for pending updates in queue
        pending_updates = self.persistence.get_pending_updates()
        
        if pending_updates:
            logger.info(f"Found {len(pending_updates)} pending updates in queue")
            await self._process_queued_update()
            return
        
        # Step 2: Fetch and process new commits
        await self._process_new_commits()
    
    async def _process_queued_update(self) -> None:
        """
        Processes and sends the next update from the queue.
        """
        next_msg = self.persistence.pop_next_update()
        
        if next_msg:
            await self._send_formatted_update(next_msg, self.DEFAULT_AUTHOR)
            logger.info("Queued update delivered successfully")
    
    async def _process_new_commits(self) -> None:
        """
        Fetches new commits and generates summaries.
        """
        # Get all commits
        commits = self.github_service.get_all_commits()
        
        # BUG FIX #4: Handle empty commit list
        if not commits:
            logger.warning("No commits retrieved from GitHub. Repository may be empty or API failed.")
            return
        
        last_sha = self.persistence.get_last_processed_sha()
        
        # Find the next commit to process
        commit_to_process = self._find_next_commit(commits, last_sha)
        
        if not commit_to_process:
            logger.info("No new commits to process")
            return
        
        # Get detailed commit information
        sha = commit_to_process["sha"]
        logger.info(f"Processing commit: {sha[:8]}...")
        
        detailed_data = self.github_service.get_commit_details(sha)
        
        if not detailed_data:
            logger.error(f"Failed to get details for commit {sha[:8]}")
            return
        
        # Generate AI summary
        updates_list = self.summarizer.analyze_and_split(detailed_data)
        
        # Send first update immediately, queue the rest
        success = await self._distribute_updates(updates_list, detailed_data)
        
        # BUG FIX #1: Only mark commit as processed if message was sent successfully
        if success:
            self.persistence.update_last_processed_sha(sha)
            logger.info(f"Commit {sha[:8]} marked as processed")
        else:
            logger.error(f"Commit {sha[:8]} NOT marked as processed due to delivery failure")
    
    def _find_next_commit(
        self,
        commits: list,
        last_sha: Optional[str]
    ) -> Optional[dict]:
        """
        Finds the next unprocessed commit.
        
        Args:
            commits: List of all commits (oldest first)
            last_sha: SHA of the last processed commit
            
        Returns:
            The next commit to process, or None if all processed
        """
        if not commits:
            return None
        
        # If no previous processing, start with the first commit
        if not last_sha:
            return commits[0]
        
        # Find the commit after last_sha
        for i, commit in enumerate(commits):
            if commit["sha"] == last_sha and i + 1 < len(commits):
                return commits[i + 1]
        
        return None
    
    async def _distribute_updates(
        self,
        updates: list,
        commit_data: dict
    ) -> bool:
        """
        Distributes updates across multiple days if needed.
        
        Args:
            updates: List of update messages from AI
            commit_data: Original commit data for author info
            
        Returns:
            True if all operations successful, False otherwise
        """
        if not updates:
            logger.warning("No updates to distribute")
            return False
        
        # Pop the first update to send now
        first_update = updates.pop(0)
        
        # Queue remaining updates for future days
        if updates:
            # BUG FIX #2: Check if queueing succeeded before proceeding
            queue_success = self.persistence.set_pending_updates(updates)
            if queue_success:
                logger.info(f"Queued {len(updates)} updates for future delivery")
            else:
                logger.error("Failed to queue remaining updates. They will be lost.")
                # Continue anyway to send at least the first update
        
        # Send the first update
        author = commit_data.get("author", self.DEFAULT_AUTHOR)
        return await self._send_formatted_update(first_update, author)
    
    async def _send_formatted_update(
        self,
        content: str,
        author: str
    ) -> bool:
        """
        Formats and sends an update message to Telegram.
        
        Args:
            content: The update content to send
            author: The developer/author name
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        date_str = datetime.now().strftime('%d.%m.%Y')
        
        # BUG FIX #5: Escape HTML special characters to prevent injection
        safe_author = html.escape(author)
        safe_content = html.escape(content)
        
        # Format the message with HTML styling
        final_message = (
            f"🚀 <b>DAILY DEVELOPMENT REPORT</b>\n\n"
            f"{safe_content}\n\n"
            f"👨‍💻 <i>Developer:</i> {safe_author}\n"
            f"📅 <i>Date:</i> {date_str}"
        )
        
        success = await self.telegram_service.send_message(final_message)
        
        if success:
            logger.info("Update message delivered successfully")
        else:
            logger.error("Failed to deliver update message")
        
        return success
    
    async def scheduler_loop(self) -> None:
        """
        Runs the scheduling loop for automated daily updates.
        
        Schedules the daily task and continuously checks for
        pending scheduled jobs.
        """
        logger.info(f"Scheduling daily updates at {self.DAILY_UPDATE_TIME}")
        
        schedule.every().day.at(self.DAILY_UPDATE_TIME).do(
            lambda: asyncio.create_task(self.run_daily_task())
        )
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)
    
    async def run(self) -> None:
        """
        Starts the bot and all its services.
        
        Runs both the Telegram polling and the scheduler loop
        concurrently using asyncio.
        """
        logger.info("Starting Investor Bot services...")
        
        try:
            await asyncio.gather(
                self.telegram_service.start_polling(),
                self.scheduler_loop()
            )
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            logger.info("Investor Bot shutting down...")


def main() -> None:
    """
    Application entry point.
    
    Creates and runs the InvestorBot instance.
    """
    bot = InvestorBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
