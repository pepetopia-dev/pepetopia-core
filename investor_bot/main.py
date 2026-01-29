import time
import schedule
import asyncio
import sys
from datetime import datetime

# Import services and utils
from src.services.github_service import GitHubService
from src.services.telegram_service import TelegramService
from src.services.summarizer import CommitSummarizer
from src.utils.persistence import PersistenceManager

class InvestorBot:
    """
    Main orchestrator class for the Investor Update Bot.
    Coordinates fetching commits, summarizing them, and sending updates via Telegram.
    """

    def __init__(self):
        print("INFO: Initializing InvestorBot components...")
        self.github_service = GitHubService()
        self.telegram_service = TelegramService()
        self.summarizer = CommitSummarizer()
        self.persistence = PersistenceManager()

    def _find_next_commit(self, commits: list) -> dict:
        """
        Determines which commit should be processed next based on the last processed SHA.
        
        Args:
            commits (list): List of commit dictionaries, sorted Oldest to Newest.
            
        Returns:
            dict: The next commit to process, or None if all are processed.
        """
        last_sha = self.persistence.get_last_processed_sha()

        # If no history exists, start with the very first commit (Oldest)
        if not last_sha:
            return commits[0] if commits else None

        # Find the index of the last processed commit
        for i, commit in enumerate(commits):
            if commit["sha"] == last_sha:
                # Check if there is a next commit in the list
                if i + 1 < len(commits):
                    return commits[i + 1]
                else:
                    return None # No new commits to process

        # If last_sha is not found (maybe history diverged), default to the last one or handle error
        # For safety, let's return the last one in the list to be safe, or logic needs adjustment.
        # Here we assume linear history mostly.
        print("WARNING: Last processed SHA not found in current history. Starting from oldest.")
        return commits[0] if commits else None

    async def run_daily_task(self):
        """
        The core logic to be executed daily.
        """
        print(f"INFO: Starting daily task at {datetime.now()}")

        # 1. Fetch all commits (Oldest -> Newest)
        commits = self.github_service.get_all_commits()
        if not commits:
            print("WARNING: No commits found in repository.")
            return

        # 2. Identify the next commit to send
        commit_to_process = self._find_next_commit(commits)

        if not commit_to_process:
            print("INFO: You are up to date! No new commits to send.")
            # Optional: Send a "No updates today" message or just stay silent.
            return

        print(f"INFO: Processing commit: {commit_to_process['message']} ({commit_to_process['sha']})")

        # 3. Generate Summary using AI
        # We pass the author name to give credit
        summary = self.summarizer.summarize(
            commit_message=commit_to_process["message"],
            author=commit_to_process["author"]
        )

        # 4. Construct the Final Message
        # We add a clean footer
        final_message = (
            f"🚀 **Günlük Geliştirme Raporu**\n\n"
            f"{summary}\n\n"
            f"👨‍💻 *Geliştirici:* {commit_to_process['author']}\n"
            f"📅 *Tarih:* {datetime.now().strftime('%d.%m.%Y')}" 
            # Note: We show TODAY's date to make it look active, as requested.
        )

        # 5. Send to Telegram
        await self.telegram_service.send_message(final_message)

        # 6. Update State (Persistence)
        self.persistence.update_last_processed_sha(commit_to_process["sha"])
        print(f"SUCCESS: Processed and saved commit {commit_to_process['sha']}")

    def job_wrapper(self):
        """
        Wrapper to run async code from synchronous schedule library.
        """
        asyncio.run(self.run_daily_task())

    def start(self):
        """
        Starts the scheduler loop.
        """
        print("INFO: Bot started. Schedule set for 20:00 daily.")
        
        # Schedule the task for 8 PM (20:00)
        # Ensure system time is correct or handle timezone in docker/server
        schedule.every().day.at("20:00").do(self.job_wrapper)

        # For testing purposes, you can uncomment the line below to run immediately on startup
        # self.job_wrapper()

        while True:
            schedule.run_pending()
            time.sleep(60) # Check every minute

if __name__ == "__main__":
    bot = InvestorBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\nINFO: Bot stopped by user.")
        sys.exit(0)