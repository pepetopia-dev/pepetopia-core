import logging
import re

logger = logging.getLogger(__name__)

def extract_url_content(text: str) -> str:
    """
    Passthrough function. Scraping has been disabled by policy.
    Returns the text as-is.
    """
    # Policy: Do NOT fetch URLs.
    return text
