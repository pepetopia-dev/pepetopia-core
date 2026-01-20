import feedparser
import logging
import random
from fake_useragent import UserAgent

# Initialize Logger
logger = logging.getLogger(__name__)

class NewsService:
    """
    Service responsible for fetching and processing crypto news from RSS feeds.
    """
    
    # List of reliable Crypto RSS Feeds
    RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptopotato.com/feed/",
        "https://decrypt.co/feed",
        "https://beincrypto.com/feed/"
    ]

    @staticmethod
    def get_recent_news(limit: int = 5) -> list:
        """
        Scans all configured RSS feeds and returns a list of unique news items.
        
        Features:
        - Uses random User-Agent to prevent 403 Forbidden errors.
        - Shuffles sources to ensure diversity.
        - Error handling for individual feed failures.

        Args:
            limit (int): The maximum number of news items to return.

        Returns:
            list: A list of dictionaries containing 'title', 'link', and 'source'.
        """
        all_news = []
        
        # Initialize UserAgent to mimic a real browser (Chrome, Firefox, etc.)
        # This prevents news sites from blocking the bot request.
        try:
            ua = UserAgent()
            user_agent_header = ua.random
        except Exception:
            # Fallback if fake-useragent fails
            user_agent_header = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

        for feed_url in NewsService.RSS_FEEDS:
            try:
                # Fetch feed with the randomized User-Agent header
                feed = feedparser.parse(feed_url, agent=user_agent_header)
                
                if not feed.entries:
                    logger.warning(f"Feed returned no entries: {feed_url}")
                    continue

                # Take the top 3 items from this feed to avoid spamming one source
                for entry in feed.entries[:3]:
                    all_news.append({
                        "title": entry.title,
                        "link": entry.link,
                        # Fallback to "Crypto News" if the feed title is missing
                        "source": feed.feed.title if 'title' in feed.feed else "Crypto News"
                    })
            except Exception as e:
                logger.error(f"Failed to fetch feed {feed_url}: {e}")
                continue
        
        if not all_news:
            logger.warning("No news found from any source.")
            return []

        # Shuffle the list to provide a mix of sources each time
        random.shuffle(all_news)
        
        # Return only the requested number of items
        return all_news[:limit]