import time
import random
from src.app_config import Config
from src.utils import logger, is_working_hours, StateManager
from src.rss_fetcher import fetch_latest_tweet
from src.ai_engine import generate_reply
from src.notifier import send_telegram_alert

def run_bot_cycle():
    """
    Single execution cycle of the bot logic.
    """
    for user in Config.TARGET_ACCOUNTS:
        logger.info(f"Checking timeline for: @{user}")
        
        tweet = fetch_latest_tweet(user)
        
        if tweet:
            if StateManager.is_seen(tweet['id']):
                logger.info(f"Tweet {tweet['id']} already processed. Skipping.")
            else:
                logger.info(f"New tweet found from @{user}! Generating reply...")
                
                # Generate AI Reply
                reply = generate_reply(tweet['content'], user)
                
                # Send Alert
                send_telegram_alert(tweet, reply)
                
                # Mark as seen
                StateManager.save_tweet_id(tweet['id'])
        
        # Random Jitter to act human-like when fetching RSS
        # Even though we use RSS, we don't want to spam Nitter instances
        time.sleep(random.uniform(5, 15))

def main():
    logger.info("Initializing Pepetopia Twitter Sentinel...")
    logger.info(f"Monitoring {len(Config.TARGET_ACCOUNTS)} accounts.")
    
    try:
        while True:
            if is_working_hours():
                run_bot_cycle()
                
                # Wait before next full cycle (approx 5 mins)
                wait_time = 300
                logger.info(f"Cycle complete. Sleeping for {wait_time} seconds.")
                time.sleep(wait_time)
            else:
                logger.info("Outside working hours. Sleeping for 1 hour.")
                time.sleep(3600)

    except KeyboardInterrupt:
        logger.info("Bot stopped manually by user.")
    except Exception as e:
        logger.critical(f"Unexpected crash: {e}")

if __name__ == "__main__":
    main()