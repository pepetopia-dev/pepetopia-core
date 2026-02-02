import logging
import re
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_url_content(text: str) -> str:
    """
    Detects if the input contains a URL. If yes, fetches the page title
    and meta description to provide context to the AI.
    """
    url_pattern = r'(https?://\S+)'
    match = re.search(url_pattern, text)
    
    if not match:
        return text  # No URL found, return original text

    url = match.group(1)
    logger.info(f"🔗 Detected URL: {url}. Fetching metadata...")

    try:
        # User-Agent is required to avoid being blocked by some sites (like Twitter/X)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract Title
        title = soup.title.string.strip() if soup.title else "No Title"
        
        # Extract Description
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                    soup.find('meta', attrs={'property': 'og:description'})
        description = meta_desc['content'].strip() if meta_desc else "No Description"

        # Enhance the input text with fetched context
        enriched_context = (
            f"Original Input: {text}\n"
            f"--- LINK CONTENT ---\n"
            f"URL: {url}\n"
            f"Page Title: {title}\n"
            f"Summary: {description}\n"
            f"--------------------"
        )
        return enriched_context

    except Exception as e:
        logger.warning(f"⚠️ Failed to fetch URL content: {e}")
        return text  # Fallback to original text on failure