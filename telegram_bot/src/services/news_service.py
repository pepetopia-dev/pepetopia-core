import feedparser
import logging
import random

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
    def get_latest_news():
        """
        Scans all RSS feeds and returns the latest news entry.
        Returns a dictionary with title, link, and source.
        """
        latest_entry = None
        
        # Shuffle to get variety from different sources
        random.shuffle(NewsService.RSS_FEEDS)

        for feed_url in NewsService.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                if feed.entries:
                    # Get the most recent entry from this feed
                    entry = feed.entries[0]
                    
                    latest_entry = {
                        "title": entry.title,
                        "link": entry.link,
                        "source": feed.feed.title if 'title' in feed.feed else "Crypto News"
                    }
                    # We found a valid entry, break and return it
                    break 
            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
                continue
        
        return latest_entry