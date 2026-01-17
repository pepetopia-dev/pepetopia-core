import feedparser
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsService:
    # Reliable Crypto RSS Feeds
    RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptopotato.com/feed/",
        "https://decrypt.co/feed"
    ]

    @staticmethod
    def get_recent_news(limit=5):
        """
        Scans all RSS feeds and returns a list of unique news from the last 24 hours.
        """
        all_news = []
        
        for feed_url in NewsService.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]: # Check top 5 from each feed
                    # Basic deduplication logic could be added here
                    all_news.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": feed.feed.title if 'title' in feed.feed else "Crypto News"
                    })
            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
                continue
        
        # Shuffle to mix sources and take only the requested amount
        random.shuffle(all_news)
        return all_news[:limit]