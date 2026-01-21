import feedparser
import random
from typing import Optional, Dict
from src.app_config import Config
from src.utils import logger

def fetch_latest_tweet(username: str) -> Optional[Dict[str, str]]:
    """
    Fetches the latest tweet from a user using Nitter RSS feeds.
    Implements a failover mechanism by rotating through available instances.

    Args:
        username (str): Twitter handle without @

    Returns:
        dict: Tweet data (id, content, link, date) or None if failed.
    """
    # Randomize instance order to distribute load
    instances = Config.NITTER_INSTANCES.copy()
    random.shuffle(instances)

    for instance in instances:
        rss_url = f"{instance}/{username}/rss"
        try:
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                latest = feed.entries[0]
                
                # Nitter uses the URL as the ID essentially
                return {
                    "id": latest.id,
                    "author": username,
                    "content": latest.title, # Nitter puts content in title
                    "link": latest.link.replace(instance, "https://twitter.com"),
                    "date": latest.published
                }
        except Exception as e:
            logger.warning(f"Failed to fetch from {instance} for {username}: {e}")
            continue
            
    logger.error(f"All Nitter instances failed for {username}")
    return None