import feedparser
import logging
import random
import asyncio # Yeni eklendi
from fake_useragent import UserAgent

# Initialize Logger
logger = logging.getLogger(__name__)

class NewsService:
    """
    Service responsible for fetching and processing crypto news from RSS feeds.
    Optimized: Uses non-blocking execution for smoother bot performance.
    """
    
    RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptopotato.com/feed/",
        "https://decrypt.co/feed",
        "https://beincrypto.com/feed/"
    ]

    @staticmethod
    def _fetch_feed_sync(url, agent):
        """
        Internal synchronous method to be run in an executor.
        """
        return feedparser.parse(url, agent=agent)

    @staticmethod
    async def get_recent_news(limit: int = 5) -> list:
        """
        Asynchronously scans RSS feeds.
        Prevents the bot from freezing during network requests.
        """
        all_news = []
        
        try:
            ua = UserAgent()
            user_agent_header = ua.random
        except Exception:
            user_agent_header = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

        loop = asyncio.get_running_loop()
        tasks = []

        # Create async tasks for all feeds
        for feed_url in NewsService.RSS_FEEDS:
            tasks.append(
                loop.run_in_executor(None, NewsService._fetch_feed_sync, feed_url, user_agent_header)
            )

        # Run all requests in parallel (Much faster!)
        feeds_results = await asyncio.gather(*tasks, return_exceptions=True)

        for feed in feeds_results:
            if isinstance(feed, Exception) or not hasattr(feed, 'entries'):
                continue
            
            if not feed.entries:
                continue

            for entry in feed.entries[:3]:
                all_news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": feed.feed.title if 'title' in feed.feed else "Crypto News"
                })

        if not all_news:
            logger.warning("No news found from any source.")
            return []

        random.shuffle(all_news)
        return all_news[:limit]