import time
import schedule
import asyncio
import sys
from datetime import datetime
from src.services.github_service import GitHubService
from src.services.telegram_service import TelegramService
from src.services.summarizer import CommitSummarizer
from src.utils.persistence import PersistenceManager

class InvestorBot:
    def __init__(self):
        print("INFO: Initializing...")
        self.github_service = GitHubService()
        self.telegram_service = TelegramService(main_bot_instance=self)
        self.summarizer = CommitSummarizer()
        self.persistence = PersistenceManager()

    async def run_daily_task(self):
        print(f"INFO: Running update task at {datetime.now()}")

        # 1. CHECK QUEUE (Hikaye devam ediyor mu?)
        pending_updates = self.persistence.get_pending_updates()
        
        if pending_updates:
            print(f"INFO: Found {len(pending_updates)} pending updates in queue. Sending next one.")
            next_msg = self.persistence.pop_next_update()
            
            # Kuyruktan gelen mesajı yazar bilgisi olmadan (veya generic) gönderebiliriz
            # Ama tutarlılık için son yazar bilgisini saklamak daha iyi olurdu. 
            # Şimdilik "Pepetopia Team" varsayalım veya önceki mantığı koruyalım.
            await self._send_formatted_update(next_msg, "pepetopia-dev") 
            return

        # 2. FETCH NEW COMMIT
        commits = self.github_service.get_all_commits()
        last_sha = self.persistence.get_last_processed_sha()
        
        commit_to_process = None
        if not last_sha:
            commit_to_process = commits[0] if commits else None
        else:
            for i, commit in enumerate(commits):
                if commit["sha"] == last_sha and i + 1 < len(commits):
                    commit_to_process = commits[i + 1]
                    break
        
        if not commit_to_process:
            print("INFO: No new commits.")
            return

        # 3. ANALYZE
        print(f"INFO: Analyzing commit {commit_to_process['sha']}...")
        detailed_data = self.github_service.get_commit_details(commit_to_process["sha"])
        
        if detailed_data:
            # AI returns a LIST of updates
            updates_list = self.summarizer.analyze_and_split(detailed_data)
            
            # Pop the first one to send NOW
            first_update = updates_list.pop(0)
            
            # Save the rest for tomorrow(s)
            if updates_list:
                self.persistence.set_pending_updates(updates_list)
                print(f"INFO: Saved {len(updates_list)} extra updates for coming days.")

            # Update SHA as processed
            self.persistence.update_last_processed_sha(commit_to_process["sha"])
            
            await self._send_formatted_update(first_update, detailed_data['author'])

    async def _send_formatted_update(self, content, author):
        """Formats the message exactly as requested."""
        date_str = datetime.now().strftime('%d.%m.%Y')
        
        # İSTENİLEN FORMAT:
        # 🚀 GÜNLÜK GELİŞTİRME RAPORU
        # [İÇERİK]
        # 👨‍💻 Geliştirici: ...
        # 📅 Tarih: ...
        
        final_message = (
            f"🚀 <b>GÜNLÜK GELİŞTİRME RAPORU</b>\n\n"
            f"{content}\n\n"
            f"👨‍💻 <i>Geliştirici:</i> {author}\n"
            f"📅 <i>Tarih:</i> {date_str}"
        )
        await self.telegram_service.send_message(final_message)

    async def scheduler_loop(self):
        schedule.every().day.at("17:00").do(lambda: asyncio.create_task(self.run_daily_task()))
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

    async def run(self):
        await asyncio.gather(
            self.telegram_service.start_polling(),
            self.scheduler_loop()
        )

if __name__ == "__main__":
    bot = InvestorBot()
    asyncio.run(bot.run())